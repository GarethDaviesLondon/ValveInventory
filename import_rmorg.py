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
        })
    return prepared, sundries


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
              "sundries": 0, "boxes": 0}

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
            for n in range(1, r["qty"] + 1):
                # only record per-valve values that differ from the lot's, so
                # a valve row says something when it is read on its own
                con.execute(
                    """INSERT INTO valve (stock_id,position,serial,manufacturer,
                                          condition,notes,added)
                       VALUES (?,?,?,?,?,?,?)""",
                    (stock_id,
                     r["position"] if r["position"] != lot["position"] else None,
                     serial_for(r["order"], n, r["qty"]),
                     r["maker"] if r["maker"] != lot["maker"] else None,
                     r["condition"] if r["condition"] != lot["condition"] else None,
                     r["notes"] if r["notes"] != lot["notes"] else None,
                     today))
                counts["valves"] += 1

    for s in sundries:
        con.execute("INSERT INTO sundry (box, description, qty, notes) VALUES (?,?,1,?)",
                    (s["box"], s["description"], s["notes"]))
        con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                    (s["box"], box_location))
        counts["sundries"] += 1

    con.commit()
    return counts


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
