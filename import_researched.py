#!/usr/bin/env python3
"""
import_researched.py - apply research results back into valves.db.

Takes the text a research assistant (e.g. Claude, given the prompt written by
valves_gui.py's Tools > Generate research prompt...) returns, and writes it
into the reference table. Only fields actually stated are touched - blanks
are left alone rather than clobbering what's already there. A
confidence_note containing hedging language ("could not confirm", "low
confidence", "plausible", ...) keeps the type at confidence='inferred'
rather than 'confirmed', so a lead gets recorded without overclaiming
certainty.

  python3 import_researched.py results.txt              # preview only
  python3 import_researched.py results.txt --yes         # apply

Expected block format (blank a field's value if not confirmed - don't
guess, don't write "unknown"):

    TYPE_NAME
    function:
    base:
    pins:
    heater_v:
    heater_a:
    va_max:
    pa_max:
    gm:
    mu:
    power_out:
    freq_max:
    typical_use:
    equivalents:
    source_url:
    confidence_note:
    ---
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

STR_FIELDS = {"function", "base", "typical_use", "equivalents"}
NUM_FIELDS = {"pins", "heater_v", "heater_a", "va_max", "pa_max", "gm", "mu", "power_out", "freq_max"}
INT_FIELDS = {"pins"}
ALL_FIELDS = ["function", "base", "pins", "heater_v", "heater_a", "va_max", "pa_max",
              "gm", "mu", "power_out", "freq_max", "typical_use", "equivalents"]
# Negative lookbehind for a letter immediately before the digits, so a type
# designation mentioned in an explanatory sentence ("...no source specific
# to EC88") doesn't get misread as the field's value.
NUM_RE = re.compile(r"(?<![A-Za-z])-?\d+\.?\d*")
HEDGE_WORDS = ("could not", "cannot confirm", "not confirmed", "low confidence",
               "plausible", "unconfirmed", "uncertain", "not verified", "no information",
               "no data", "not found", "no source", "no datasheet")
# A field's whole value reading as "couldn't find this" rather than an actual
# answer - e.g. Claude writing "va_max: NOT FOUND - no reliable source
# specific to EC88" instead of leaving the value blank as the prompt asks.
# Treated exactly like a blank value: skip the field, don't record anything.
NOT_FOUND_RE = re.compile(
    r"\b(not found|no reliable source|no data\b|no information|not available|"
    r"unknown|n/?a\b|no source|not confirmed|unconfirmed|no datasheet|"
    r"could not (?:find|confirm|verify)|cannot (?:find|confirm|verify))\b", re.I)


def parse_num(raw, is_int):
    """Extract the first numeric value from `raw` using NUM_RE; return int, float, or None if absent."""
    m = NUM_RE.search(raw)
    if not m:
        return None
    val = float(m.group())
    return int(round(val)) if is_int else val


def parse_blocks(text):
    """Split raw research-reply text into per-type records keyed by normalized type_key.

    Returns {type_key: (rec, source_url, confidence_note)} where `rec` is a
    dict of the field values actually stated (see ALL_FIELDS) - fields left
    blank, or whose value reads as "not found" (NOT_FOUND_RE), are omitted
    rather than recorded. Unrecognized keys/lines are ignored.
    """
    # Tolerate a pasted-from-chat reply rather than a clean file: CRLF line
    # endings, and a "---" separator with stray trailing spaces or an extra
    # blank line around it (an exact "\n---\n" match missed those).
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b.strip("\n") for b in re.split(r"\n[ \t]*-{3,}[ \t]*\n", text) if b.strip()]
    records = {}
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip()]
        if not lines:
            continue
        key = V.norm(re.split(r"[\s:(]", lines[0])[0])
        if not key:
            continue
        rec, source, conf_note = {}, None, None
        for line in lines[1:]:
            if ":" not in line:
                continue
            field, _, val = line.partition(":")
            field, val = field.strip().lower(), val.strip()
            if not val or (field != "confidence_note" and NOT_FOUND_RE.search(val)):
                continue
            if field == "source_url":
                source = val
            elif field == "confidence_note":
                conf_note = val
            elif field in NUM_FIELDS:
                n = parse_num(val, field in INT_FIELDS)
                if n is not None:
                    rec[field] = n
            elif field in STR_FIELDS:
                rec[field] = val
        records[key] = (rec, source, conf_note)
    return records


def apply_records(con, records, dry_run=True):
    """Write parsed `records` into valve_type, or just print what would change if dry_run.

    For each record: skip type_keys not present in the DB (-> missing) and
    ones with no fields beyond equivalents (-> skipped); otherwise update
    the stated fields, append source/confidence_note to notes (prepended to
    any existing notes), and mark confidence='confirmed' unless the
    confidence_note reads as hedged (see HEDGE_WORDS). Returns
    (applied, skipped, missing) lists of type_keys.
    """
    applied, skipped, missing = [], [], []
    for key, (rec, source, conf_note) in records.items():
        row = con.execute("SELECT type_key, notes FROM valve_type WHERE type_key=?", (key,)).fetchone()
        if not row:
            missing.append(key)
            continue
        meaningful = [f for f in rec if f != "equivalents"]
        if not meaningful:
            skipped.append(key)
            continue
        confirmed = not (conf_note and any(h in conf_note.lower() for h in HEDGE_WORDS))
        print(f"{'applying' if not dry_run else 'would apply'} {key}: "
              f"{', '.join(f'{k}={v}' for k, v in rec.items())} "
              f"[{'confirmed' if confirmed else 'lead only'}]")
        if dry_run:
            applied.append(key)
            continue
        sets, args = [], []
        for field in ALL_FIELDS:
            if field in rec:
                sets.append(f"{field}=?")
                args.append(rec[field])
        note_bits = []
        if conf_note:
            note_bits.append(f"Research note: {conf_note}")
        if source:
            note_bits.append(f"Source: {source}")
            sets.append("datasheet_url=?")
            args.append(source)
        prior = (row["notes"] or "").strip()
        if note_bits:
            full_note = "\n".join(note_bits) + (("\n\n" + prior) if prior else "")
            sets.append("notes=?")
            args.append(full_note)
        if confirmed:
            sets.append("confidence='confirmed'")
        args.append(key)
        con.execute(f"UPDATE valve_type SET {','.join(sets)} WHERE type_key=?", args)
        applied.append(key)
    return applied, skipped, missing


def main():
    """CLI entry point: parse the research-reply file and apply it (--yes) or preview it (default)."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file")
    p.add_argument("--db", default=V.DB_DEFAULT)
    p.add_argument("--yes", action="store_true", help="apply changes (default is dry-run preview)")
    a = p.parse_args()

    try:
        # Research text may contain non-ASCII (accented names, symbols); widen
        # stdout so printing it doesn't crash on a narrower console encoding.
        # reconfigure() is Python 3.7+; AttributeError guards older stdout wrappers.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    with open(a.file, encoding="utf-8") as f:
        records = parse_blocks(f.read())

    con = V.init_db(a.db)
    applied, skipped, missing = apply_records(con, records, dry_run=not a.yes)

    if a.yes:
        con.commit()
        print(f"\napplied {len(applied)} types")
    else:
        print(f"\n{len(records)} records parsed - {len(applied)} would be applied. "
              f"Re-run with --yes to write them.")
    if skipped:
        print(f"skipped (no data beyond equivalents): {', '.join(skipped)}")
    if missing:
        print(f"WARNING - type_key not found in DB: {', '.join(missing)}")
    con.close()


if __name__ == "__main__":
    main()
