#!/usr/bin/env python3
"""
import_rmorg.py - load the RMORG collection spreadsheet into a valves.db.

The RMORG sheet is a single flat table (one worksheet, Portuguese headers)
with one row per physical valve rather than per lot: each row carries its own
order number in "NºOrd.", its own shelf position, and its own condition. That
is exactly the shape the v1.4 individual-valve model was added for, so this
importer targets it directly - every row becomes one `valve` row with the
order number as its serial, hung off the `stock` lot it belongs to.

Lots are formed by grouping rows that agree on everything that identifies a
lot (type, box, position, maker, condition, origin, the two alternative
designations): forty-two ECH81 in the same place from the same source become
one lot of forty-two with forty-two individual valves under it, not
forty-two lots of one. --no-group turns that off for a faithful
one-lot-per-row import.

Reference data the sheet carries at type level (base, function, heater,
equivalents) is written into valve_type, but only into columns that are
still empty - the sheet never overwrites what a datasheet already
established. Types the sheet says nothing about fall back to
valvelib.classify() exactly as 'add' and 'import-csv' do, and are left at
confidence='inferred' either way, since a stock list is not a datasheet.

  python3 import_rmorg.py                              # sheet -> valves_rmorg.db
  python3 import_rmorg.py --dry-run                    # report, write nothing
  python3 import_rmorg.py book.xlsx out.db             # explicit paths
  python3 import_rmorg.py --append valves.db           # into an existing DB
  python3 import_rmorg.py --no-group                   # one lot per sheet row
  python3 import_rmorg.py --notes-only valves.db       # per-valve notes + tests

Writing a fresh database deletes any file already at that path, so the
default output is valves_rmorg.db rather than valves.db - importing does not
tread on the working database unless you name it.
"""
import argparse
import collections
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

SRC_DEFAULT = os.path.join("sourceinfo", "RMORG Python 08-2026.xlsx")
DB_DEFAULT = "valves_rmorg.db"

# Column positions in the single worksheet, 0-based. Declared explicitly
# rather than matched on the header text: the headers carry accents, stray
# commas and trailing spaces ("Div,", "Potencia W "), and one column has no
# header at all.
COLS = {
    "type":      0,   # TIPO/Ref
    "type1":     1,   # Outra Ref2      - alternative designation as marked
    "box":       2,   # Localização
    "position":  3,   # Div,            - division within the box
    "qty":       4,   # Qtd.            - blank means one
    "order":     5,   # NºOrd.          - per-valve accession number
    "maker":     6,   # Marca
    "equiv":     7,   # Equiv.
    "origin":    8,   # Origem          - who it came from
    "base":      9,   # Base            - B9A, K8A, ...
    "base_name": 10,  # Base Nome       - Noval, Octal, Rimlock, ...
    "function":  11,  # Função
    "voltage":   12,  # Tensão V / Ω
    "current":   13,  # Corrente A
    "power":     14,  # Potencia W
    "state":     15,  # ESTADO - Q - mA/V
    "obs":       16,  # Obs.
    "notes":     17,  # Notas
}

# The whole of one row reads "COMPONENTES" where a type should be: those rows
# record a box of loose components rather than a valve, and become sundries.
COMPONENTS = "COMPONENTES"

# ESTADO holds two different kinds of thing: a plain statement of condition,
# and a tester reading. Anything in this table is a condition and lands in
# stock.condition; everything else is a measurement and is kept verbatim in
# stock.test_values, since "OK CT160" and "120-135% - TV2" name the tester
# and mean nothing once paraphrased.
CONDITIONS = {
    "NOS": "NOS",
    "USADA": "used", "USADAS": "used", "USADOS": "used",
    "FRACA": "weak", "FRACAS": "weak",
    "VAL OFF": "heater open", "OFF FILAMENTO": "heater open",
    "FILAMENTO OFF": "heater open",
    "MAUS CONTAC.": "bad contacts",
    "S/CX": "unboxed",
}

# Where a designation survives normalisation as nothing at all - the sheet has
# one valve recorded only as "??" - it still describes a real valve on a real
# shelf, so it is filed under this key rather than dropped or left with a NULL
# type_key that no foreign key can point at.
UNIDENTIFIED = "UNIDENTIFIED"

# Base Nome -> the base code valve_type.base wants, for the rows that name the
# base in words but leave the code column empty.
BASE_NAMES = {
    "NOVAL": "B9A", "MINI": "B7G", "MINIATURA": "B7G",
    "OCTAL": "K8A", "RIMLOCK": "B8A", "LOCTAL": "B8B",
}


def cell(v):
    """Normalise one openpyxl value to a stripped string ("" when empty).

    Non-breaking spaces are folded to ordinary ones: the Função column is
    full of them (it was pasted in from a web page) and they would otherwise
    make two spellings of the same function look like different values.
    """
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v).replace("\xa0", " ")).strip()


def parse_qty(s):
    """Quantity as an int, defaulting to 1 for blank or unparseable cells.

    Blank is by far the common case - the sheet only fills Qtd. in when a
    row stands for more than one valve.
    """
    if not s:
        return 1
    try:
        return max(1, int(float(s.replace(",", "."))))
    except ValueError:
        return 1


def parse_number(s, limit):
    """A bare number from a free-text cell, or None if it isn't one.

    `limit` rejects a value too large to be the quantity asked for: the
    voltage column doubles as an ohms column for barretters and ballast
    lamps, so "20.000" there is a resistance, not a heater rating, and
    guessing wrong is worse than leaving the field empty for the sake of
    eighteen rows. Whatever is rejected still reaches valve_type.notes, so
    nothing in the sheet is lost.
    """
    if not s:
        return None
    m = re.fullmatch(r"([\d]+(?:[.,]\d+)?)", s.strip())
    if not m:
        return None
    try:
        n = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    return n if 0 < n <= limit else None


def serial_for(order, n, total):
    """The serial to give copy `n` of `total` for one order number.

    A row standing for a single valve takes the order number as it is. A row
    standing for several shares one order number between them, so each copy
    gets a suffix ("2093/1", "2093/2") - the alternative is several valves
    with identical serials, which defeats the point of recording one.
    """
    if not order:
        return None
    return order if total == 1 else f"{order}/{n}"


# --------------------------------------------------------------------------
# Reading the sheet
# --------------------------------------------------------------------------

def read_rows(path):
    """Read the worksheet into (row number, {field: text}) pairs.

    Blank rows and the header are dropped, as are rows with nothing usable in
    them. A row with no type but an alternative designation is promoted -
    the sheet has one such - and a row with no designation at all in either
    column is reported to the caller as skipped rather than silently lost.
    """
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    out, skipped = [], []
    for ridx, raw in enumerate(ws.iter_rows(values_only=True), start=1):
        if ridx == 1 or not any(c not in (None, "") for c in raw):
            continue
        r = {name: cell(raw[i]) if i < len(raw) else "" for name, i in COLS.items()}
        if not r["type"] and r["type1"]:
            r["type"], r["type1"] = r["type1"], ""
        if not r["type"]:
            skipped.append((ridx, "no type designation in either column"))
            continue
        out.append((ridx, r))
    return out, skipped


def type_records(rows):
    """Accumulate what the sheet knows about each valve TYPE, keyed by type_key.

    Several hundred rows describe the same eight hundred types, disagreeing
    here and there - three spellings of one function, a base recorded as
    "s/Cx" on one row and "B9A" on the next. For every field the longest
    value seen wins, which reliably picks the fullest description ("Vacuum
    Pentode RF/IF-Stage Controlling (mu)" over "Vacuum Pentode") and, for the
    base, the real code over a stray note. The display name is the opposite:
    the most common spelling, tie-broken shortest, so a type shows as "6L6"
    rather than "6L6 CRC-6L6".
    """
    names = collections.defaultdict(collections.Counter)
    best = collections.defaultdict(dict)
    raw_units = collections.defaultdict(set)
    for _ridx, r in rows:
        key = V.norm(r["type"]) or UNIDENTIFIED
        names[key][r["type"]] += 1
        base = r["base"] or BASE_NAMES.get(r["base_name"].upper(), r["base_name"])
        for field, value in (("base", base), ("function", r["function"]),
                             ("equivalents", r["equiv"])):
            if value and len(value) > len(best[key].get(field, "")):
                best[key][field] = value
        for label, value in (("V/ohm", r["voltage"]), ("A", r["current"]),
                             ("W", r["power"])):
            if value:
                raw_units[key].add(f"{label}: {value}")

    out = {}
    for key, counter in names.items():
        rec = dict(best[key])
        rec["name"] = min(counter.most_common(), key=lambda kv: (-kv[1], len(kv[0])))[0]
        # the unit columns are per-row rather than per-type, so they were
        # gathered as raw text; parse what can be parsed, keep all of it
        for text in sorted(raw_units.get(key, ())):
            label, _, value = text.partition(": ")
            if label == "V/ohm" and rec.get("heater_v") is None:
                rec["heater_v"] = parse_number(value, 120)
            elif label == "A" and rec.get("heater_a") is None:
                rec["heater_a"] = parse_number(value, 5)
            elif label == "W" and rec.get("pa_max") is None:
                rec["pa_max"] = parse_number(value, 100000)
        if raw_units.get(key):
            rec["notes"] = "from RMORG sheet - " + "; ".join(sorted(raw_units[key]))
        out[key] = rec
    return out


def lot_key(r, group):
    """The grouping key for a row: everything that makes one lot one lot.

    Two rows join the same lot when they agree on all of it. With --group off
    the row number is folded in, which makes every key unique and so gives
    one lot per row.
    """
    key = (V.norm(r["type"]) or UNIDENTIFIED, r["box"], r["position"], r["maker"],
           r["condition"], r["origin"], r["type1"], r["type2"])
    return key if group else key + (r["_row"],)


def prepare(rows, unknown_box):
    """Turn sheet rows into lot-shaped dicts, splitting off the sundries.

    Per row: ESTADO is sorted into condition or test values, Obs. and Notas
    into the two free-text columns, and a row with no location at all is
    parked in `unknown_box` (the column is NOT NULL, and a hundred-odd rows
    leave it blank) rather than dropped.
    """
    prepared, sundries = [], []
    for ridx, r in rows:
        if r["type"].upper() == COMPONENTS:
            sundries.append({"box": r["box"] or unknown_box,
                             "description": "loose components (unsorted)",
                             "notes": f"RMORG sheet row {ridx}"})
            continue
        state = r["state"]
        condition = CONDITIONS.get(state.upper())
        prepared.append({
            "_row": ridx,
            "type": r["type"],
            "box": r["box"] or unknown_box,
            "position": r["position"] or None,
            "qty": parse_qty(r["qty"]),
            "order": r["order"] or None,
            "maker": r["maker"] or None,
            "condition": condition,
            "test_values": None if condition or not state else state,
            "type1": r["type1"] or None,
            "type2": r["equiv"] if r["equiv"] and r["equiv"].upper() != COMPONENTS else None,
            "origin": r["origin"] or None,
            "other": r["obs"] or None,
            "notes": r["notes"] or None,
            # the three free-text columns kept verbatim: the per-valve note and
            # the test parser both read them, and neither wants them already
            # sorted into lot columns
            "_state": state,
            "_obs": r["obs"],
            "_notas": r["notes"],
        })
    return prepared, sundries


# --------------------------------------------------------------------------
# Per-valve free text, and the tests hidden in it
# --------------------------------------------------------------------------

# ESTADO holds a verdict as often as a condition, and Obs./Notas carry a few
# more. Longest key first so "MUITO FRACA" beats "FRACA" and "FILAMENTO OFF"
# is not read as a bare "OFF".
VERDICTS = [
    ("MUITO FRACA",     "very weak"),
    ("FILAMENTO OFF",   "heater open"),
    ("OFF FILAMENTO",   "heater open"),
    ("OFF QUANDO QUENTE", "fails when hot"),
    ("MAUS CONTAC",     "bad contacts"),
    ("TESTADO OK",      "good"),
    ("TESTADA OK",      "good"),
    ("TRIODO FRACO",    "triode section weak"),
    ("FUGA DE S",       "leakage when cold"),
    ("AVARIADA",        "failed"),
    ("RUIDOSA",         "noisy"),
    ("REPARADA",        "repaired"),
    ("VAL OFF",         "heater open"),
    ("FRACA",           "weak"),
    ("FRACO",           "weak"),
    ("OK",              "good"),
]

# Rows whose free text carries readings worth typed columns. Declared per
# sheet row rather than parsed, because the same "a/b" shape means two
# different things: on a 43, a 25A6 or a 1625 - all single-section valves -
# "2.4/2.35 ... 15/18Vg" is one valve measured at two grid biases, so it
# becomes two test rows with different vg and no section; on the ELL80, a
# genuine double output pentode, "25/29mA" really is the two sections. A
# parser that guessed would get one of those wrong, and these figures are the
# sort a rebuild gets designed around.
#
# Each entry is a list of test dicts. Grid bias is written negative: the sheet
# omits the sign, but a control grid in normal service is negative, and a
# positive figure in this column would read as a fault.
EXPLICIT_TESTS = {
    216:  [{"gm": 5.0, "notes": "sheet reads '5 mho'; taken as 5 mA/V"}],
    229:  [{"gm": 12.0}],
    433:  [{"tester": "TV2", "gm_pct": 100}],
    438:  [{"tester": "AVO CT160", "verdict": "good", "gm": 2.4, "vg": -15.0, "ia": 33.0},
           {"tester": "AVO CT160", "verdict": "good", "gm": 2.35, "vg": -18.0}],
    572:  [{"gm_pct": 40, "notes": "sheet reads '40%-45%'; low end of the stated range"}],
    845:  [{"tester": "TV2", "gm_pct": 120,
            "notes": "sheet reads '120-135% - TV2'; low end of the stated range"}],
    846:  [{"tester": "TV2", "gm_pct": 130}],
    891:  [{"tester": "TV2", "notes": "sheet reads 'teste noTV2/U, shunte a 10 %a 70'"}],
    924:  [{"tester": "AVO CT160", "verdict": "good", "gm": 6.8, "vg": -15.0, "ia": 83.0},
           {"tester": "AVO CT160", "verdict": "good", "gm": 6.5, "vg": -18.0}],
    998:  [{"tester": "AVO CT160", "verdict": "good", "gm": 2.0, "ia": 33.0},
           {"tester": "AVO CT160", "verdict": "good", "gm": 2.35, "ia": 33.0}],
    1422: [{"tester": "AVO CT160", "verdict": "good", "va": 250.0, "vg": -5.8,
            "gm": 6.9, "ia": 25.0,
            "notes": "second section read 29 mA; screen at 200 V"}],
}

# Free text that states a condition or a packing detail rather than a test.
# Matched whole (uppercased) so "NOS" does not suppress "NOS, OK CT160".
NOT_A_TEST = {"NOS", "USADA", "USADAS", "USADOS", "S/CX", "SNO1918",
              "SCREEN-GRID TETRODE", "STROBE TUBE", "CX EM LATA AL-"}

_GM_RE = re.compile(r"(\d+[.,]?\d*)\s*mA/V", re.I)
_PCT_RE = re.compile(r"(\d+)\s*%")


def valve_note(r):
    """Compose one individual valve's note from the sheet's free-text columns.

    Obs. and Notas are what the owner wrote about THIS valve - "s/Cx"
    (no box), "c/ top" (with top cap), "Outra em CASA" (another one at
    home) - so they belong on the valve rather than pooled onto the lot.
    Each is labelled with the column it came from, because "Cx original"
    under Obs. and "FOTO" under Notas are different kinds of remark and the
    distinction is lost once they are run together.

    Returns None when the row said nothing.
    """
    bits = []
    if r.get("_obs"):
        bits.append(f"Obs: {r['_obs']}")
    if r.get("_notas"):
        bits.append(f"Notas: {r['_notas']}")
    return " | ".join(bits) or None


def parse_tests(r):
    """Return a list of valve_test field dicts for one sheet row.

    An explicit entry in EXPLICIT_TESTS wins outright. Otherwise the three
    free-text columns are read for a tester name, a verdict and any bare
    reading, and a test is emitted only if at least one of those turned up -
    "NOS" on its own is a statement of condition, not a measurement.

    tested_on is deliberately left unset: the sheet records no test dates, and
    stamping today's date would assert that every one of these was measured on
    the day of the import. The source text travels in notes either way, so
    nothing here has to be taken on trust.
    """
    tests = [dict(t) for t in EXPLICIT_TESTS.get(r["_row"], [])]
    raw = " | ".join(x for x in (r.get("_state"), r.get("_obs"), r.get("_notas")) if x)
    if not tests:
        up = raw.upper()
        if up.strip() in NOT_A_TEST:
            return []
        t = {}
        if "CT160" in up.replace(" ", ""):
            t["tester"] = "AVO CT160"
        elif "TV2" in up:
            t["tester"] = "TV2"
        elif re.search(r"\bTV\b", up):
            t["tester"] = "TV"
        for needle, verdict in VERDICTS:
            if needle in up:
                t["verdict"] = verdict
                break
        m = _GM_RE.search(raw)
        if m:
            t["gm"] = float(m.group(1).replace(",", "."))
        m = _PCT_RE.search(raw)
        if m:
            t["gm_pct"] = float(m.group(1))
        if not t:
            return []
        tests = [t]
    for t in tests:
        note = t.get("notes")
        t["notes"] = f"from RMORG sheet row {r['_row']}: {raw}" + (f" ({note})" if note else "")
    return tests


TEST_COLS = ("tester", "section", "va", "vg", "bias_mode", "ia", "ig2", "gm",
             "gm_pct", "emission_pct", "gas_ua", "insulation_mohm",
             "heater_cathode", "shorts", "verdict", "notes")


def insert_test(con, valve_id, t):
    """Insert one valve_test row, leaving tested_on NULL (see parse_tests)."""
    cols = [c for c in TEST_COLS if t.get(c) is not None]
    con.execute(
        f"INSERT INTO valve_test (valve_id,{','.join(cols)}) "
        f"VALUES (?{',?' * len(cols)})", [valve_id] + [t[c] for c in cols])


def group_lots(prepared, group):
    """Collapse prepared rows into lots, each carrying the rows that made it.

    Free text is not part of the grouping key - two otherwise identical rows
    differing only in an observation still belong in the same lot - so the
    lot takes the first non-empty value it sees for each of those, and the
    rest travel with the individual valves that mentioned them.
    """
    lots = collections.OrderedDict()
    for r in prepared:
        k = lot_key(r, group)
        lot = lots.get(k)
        if lot is None:
            lot = lots[k] = {"type": r["type"], "box": r["box"], "position": r["position"],
                             "maker": r["maker"], "condition": r["condition"],
                             "type1": r["type1"], "type2": r["type2"],
                             "origin": r["origin"], "test_values": r["test_values"],
                             "other": r["other"], "notes": r["notes"],
                             "qty": 0, "rows": []}
        for field in ("test_values", "other", "notes"):
            if lot[field] is None:
                lot[field] = r[field]
        lot["qty"] += r["qty"]
        lot["rows"].append(r)
    return list(lots.values())


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

def write(con, lots, sundries, types, box_location):
    """Write types, lots, individual valves and sundries into an open database.

    valve_type rows are created where the type is new (from the sheet where
    it says something, from V.classify() where it doesn't) and topped up
    where it already exists but has empty columns the sheet can fill.
    Existing values are never overwritten.

    Every lot gets one `valve` row per valve it holds, carrying that valve's
    own order number, position and - where the sheet recorded them per row
    rather than per lot - its own maker, condition and notes. That is the
    point of this import: the sheet's unit is the valve, so the database's
    should be too.
    """
    today = datetime.date.today().isoformat()
    counts = {"types_new": 0, "types_filled": 0, "lots": 0, "valves": 0,
              "sundries": 0, "boxes": 0, "tests": 0}

    for lot in lots:
        key = V.norm(lot["type"]) or UNIDENTIFIED
        row = con.execute("SELECT * FROM valve_type WHERE type_key=?", (key,)).fetchone()
        rec = types.get(key, {})
        if row is None:
            inf = V.classify(lot["type"])
            con.execute(
                """INSERT INTO valve_type (type_key,name,function,family,base,
                       heater_v,heater_a,pa_max,equivalents,notes,confidence)
                   VALUES (?,?,?,?,?,?,?,?,?,?,'inferred')""",
                (key, rec.get("name") or lot["type"],
                 rec.get("function") or inf.get("function"), inf.get("family"),
                 rec.get("base"),
                 rec.get("heater_v") if rec.get("heater_v") is not None else inf.get("heater_v"),
                 rec.get("heater_a") if rec.get("heater_a") is not None else inf.get("heater_a"),
                 rec.get("pa_max"), rec.get("equivalents"), rec.get("notes")))
            counts["types_new"] += 1
        else:
            fill = {c: rec[c] for c in ("function", "base", "heater_v", "heater_a",
                                        "pa_max", "equivalents")
                    if rec.get(c) is not None and row[c] is None}
            if fill:
                con.execute("UPDATE valve_type SET "
                            + ",".join(f"{c}=?" for c in fill)
                            + " WHERE type_key=?", list(fill.values()) + [key])
                counts["types_filled"] += 1

        cur = con.execute(
            """INSERT INTO stock (type_key,box,position,qty,manufacturer,condition,
                                  type1,type2,origin,test_values,other,date_added,notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (key, lot["box"], lot["position"], lot["qty"], lot["maker"], lot["condition"],
             lot["type1"], lot["type2"], lot["origin"], lot["test_values"],
             lot["other"], today, lot["notes"]))
        stock_id = cur.lastrowid
        counts["lots"] += 1
        if con.execute("SELECT 1 FROM box WHERE box=?", (lot["box"],)).fetchone() is None:
            counts["boxes"] += 1
        con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                    (lot["box"], box_location))

        for r in lot["rows"]:
            note = valve_note(r)
            tests = parse_tests(r)
            for n in range(1, r["qty"] + 1):
                # position/maker/condition are only worth repeating on the valve
                # when they differ from the lot's; the note is not, because it is
                # what the owner wrote about THIS valve and reads as nothing
                # once it is pooled onto the lot with its neighbours'
                cur = con.execute(
                    """INSERT INTO valve (stock_id,position,serial,manufacturer,
                                          condition,notes,added)
                       VALUES (?,?,?,?,?,?,?)""",
                    (stock_id,
                     r["position"] if r["position"] != lot["position"] else None,
                     serial_for(r["order"], n, r["qty"]),
                     r["maker"] if r["maker"] != lot["maker"] else None,
                     r["condition"] if r["condition"] != lot["condition"] else None,
                     note, today))
                counts["valves"] += 1
                for t in tests:
                    insert_test(con, cur.lastrowid, t)
                    counts["tests"] += 1

    for s in sundries:
        con.execute("INSERT INTO sundry (box, description, qty, notes) VALUES (?,?,1,?)",
                    (s["box"], s["description"], s["notes"]))
        con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                    (s["box"], box_location))
        counts["sundries"] += 1

    con.commit()
    return counts


def apply_notes(con, lots, dry_run):
    """Add the per-valve notes and tests to a database that already holds them.

    For a database this script built, the mapping back from sheet row to valve
    row is exact rather than guessed: lots were inserted in the order
    group_lots returns them and valves in the order each lot lists its rows,
    both into empty AUTOINCREMENT tables, so lot i is stock id i and the valve
    rows follow in the same sequence. Every match is checked against the
    stored serial before anything is written, and a single disagreement aborts
    the whole run - a mismatch would mean this is not the database that sheet
    built, and writing notes onto the wrong valves is far worse than doing
    nothing.

    Existing note text is kept: the sheet's note is prepended to it, and a
    valve already carrying it is left alone, so a second run changes nothing.
    Tests are only added to valves that have none, for the same reason.
    valve_type is never touched - the reference data researched into it stands.
    """
    pairs, vid = [], 0
    for i, lot in enumerate(lots, start=1):
        for r in lot["rows"]:
            for n in range(1, r["qty"] + 1):
                vid += 1
                pairs.append((vid, i, r, serial_for(r["order"], n, r["qty"])))

    have = {row["id"]: row for row in
            con.execute("SELECT id, stock_id, serial, notes FROM valve")}
    if len(have) != len(pairs):
        raise SystemExit(
            "database holds %d valves, the sheet makes %d - not the database "
            "this sheet built, refusing to touch it" % (len(have), len(pairs)))

    bad = [(vid, serial, have.get(vid))
           for vid, stock_id, _r, serial in pairs
           if vid not in have or have[vid]["stock_id"] != stock_id
           or have[vid]["serial"] != serial]
    if bad:
        print("  %d valve row(s) do not line up with the sheet, e.g.:" % len(bad))
        for vid, want, got in bad[:5]:
            print("    valve %s: sheet says serial %r, database has %r"
                  % (vid, want, got["serial"] if got else None))
        raise SystemExit("refusing to write notes onto valves that may be the wrong ones")

    noted = tested = skipped = 0
    for vid, _stock_id, r, _serial in pairs:
        note = valve_note(r)
        if note:
            old = have[vid]["notes"]
            if old and note in old:
                skipped += 1
            else:
                if not dry_run:
                    con.execute("UPDATE valve SET notes=? WHERE id=?",
                                (note if not old else note + " | " + old, vid))
                noted += 1
        tests = parse_tests(r)
        if tests and not con.execute(
                "SELECT 1 FROM valve_test WHERE valve_id=?", (vid,)).fetchone():
            for t in tests:
                if not dry_run:
                    insert_test(con, vid, t)
                tested += 1
    if not dry_run:
        con.commit()
    return noted, tested, skipped


def main():
    ap = argparse.ArgumentParser(
        description="Load the RMORG collection spreadsheet into a valves.db.")
    ap.add_argument("source", nargs="?", default=SRC_DEFAULT, help="the .xlsx to read")
    ap.add_argument("db", nargs="?", default=DB_DEFAULT, help="the database to write")
    ap.add_argument("--append", action="store_true",
                    help="add to an existing database instead of recreating it")
    ap.add_argument("--no-group", dest="group", action="store_false",
                    help="one lot per spreadsheet row, rather than merging identical ones")
    ap.add_argument("--unknown-box", default="unsorted",
                    help="box name for rows with no location (default: unsorted)")
    ap.add_argument("--box-location", default=None,
                    help="location to record for boxes this import creates")
    ap.add_argument("--notes-only", action="store_true",
                    help="add per-valve notes and tests to an existing database, "
                         "leaving everything else (valve_type especially) alone")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be imported and write nothing")
    a = ap.parse_args()

    if not os.path.exists(a.source):
        sys.exit(f"no such spreadsheet: {a.source}")

    rows, skipped = read_rows(a.source)
    types = type_records(rows)
    prepared, sundries = prepare(rows, a.unknown_box)
    lots = group_lots(prepared, a.group)
    valves = sum(r["qty"] for r in prepared)

    print(f"{a.source}")
    print(f"  {len(rows)} usable rows -> {len(lots)} lot(s), {valves} individual valve(s), "
          f"{len(types)} type(s), {len(sundries)} sundry item(s)")
    if skipped:
        print(f"  {len(skipped)} row(s) skipped:")
        for ridx, why in skipped:
            print(f"    row {ridx}: {why}")
    if a.notes_only:
        if not os.path.exists(a.db):
            sys.exit("no such database: " + a.db)
        con = V.connect(a.db)
        noted, tested, skipped = apply_notes(con, lots, a.dry_run)
        con.close()
        verb = "would add" if a.dry_run else "added"
        print("")
        print("%s notes to %d valve(s) and %d test result(s) in %s"
              % (verb, noted, tested, a.db))
        if skipped:
            print("  %d valve(s) already carried their note - left alone" % skipped)
        if a.dry_run:
            print("  --dry-run: nothing written")
        return

    if a.dry_run:
        print("\n  --dry-run: nothing written")
        return

    if not a.append and os.path.exists(a.db):
        os.remove(a.db)
    con = V.init_db(a.db)
    counts = write(con, lots, sundries, types, a.box_location)
    con.close()

    print(f"\nwrote {a.db}")
    print(f"  {counts['lots']} lot(s), {counts['valves']} individual valve(s)")
    print(f"  {counts['types_new']} new type(s), {counts['types_filled']} existing "
          f"type(s) gained reference data from the sheet")
    print(f"  {counts['boxes']} new box(es), {counts['sundries']} sundry item(s)")
    print(f"\n  python3 valves.py --db {a.db} box 24      # list one box")
    print(f"  python3 valves.py --db {a.db} check         # lots vs individual counts")


if __name__ == "__main__":
    main()
