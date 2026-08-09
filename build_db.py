"""
build_db.py - one-off conversion of StockList (38 tabs, one per box)
into the normalised valves.db.

Each sheet has its own column layout, so the mapping is declared explicitly
per sheet below rather than guessed.
"""

import os
import re
import sys
import datetime
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

SRC = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/StockList__version_1_.xlsx"
DB = sys.argv[2] if len(sys.argv) > 2 else "valves.db"

# Known manufacturers - used to tell a maker cell from an equivalent cell,
# because several sheets use the same column for both.
MAKERS = {
    "MULLARD", "MAZDA", "PINNACLE", "OSRAM", "MARCONI", "GEC", "BRIMAR",
    "SVETLANA", "JJ", "SOVTEK", "MARSHALL", "PHILLIPS", "PHILIPS", "DRAGON",
    "DEBANKS", "EVEREADY", "EVERREADY", "AMPEREX", "PENTALABS", "TOSHIBA",
    "REC", "COSSOR", "SIXSIXTY", "EIMAC", "VOSKHOD", "GE", "TEONEX", "ZAPEX",
    "THORNAEI", "AEI", "RUSSIAN", "CHINESE", "UNMARKED", "NOS",
}

# Text that marks a non-valve item.
SUNDRY_HINTS = ("SOCKET", "SCREENING CAN", "VARIOUS SOCKETS", "XTAL", "CRYSTAL",
                "CHIMNEY", "CHIMEY", "DATA")

# ---------------------------------------------------------------------------
# Per-sheet column maps.
#   t = type, q = qty, m = manufacturer, e = equivalent, n = notes, x = ignore
# Index is 0-based column position.
# ---------------------------------------------------------------------------
LAYOUTS = {
    "Box 1 May 2022":   {"t": 0, "q": 1, "me": [2, 3, 4, 5], "n": [6], "skip_rows": [1]},
    "Box 2 May 2022":   {"t": 0, "q": 1, "me": [2, 3, 4, 5], "n": [6]},
    "Box 3 May 2022":   {"t": 0, "q": 1, "me": [2, 3], "n": [4]},
    "Box4 May2022":     {"t": 0, "q": 1, "me": [2], "n": [3]},
    "Box 5 May2022":    {"t": 0, "q": 1, "me": [2], "n": [3]},
    "Box 6 May 2022":   {"t": 0, "q": 1, "me": [2], "n": [3]},
    "Box 7 May 2020":   {"t": 0, "q": 1, "me": [], "n": [2]},
    "BOX8":             {"t": 0, "q": None, "me": [1], "n": [2], "qty_or_maker": 1},
    "Box9":             {"t": 0, "q": 1, "me": [], "n": [2, 3]},
    "Box 10":           {"t": 0, "q": 1, "me": [2, 3], "n": [4]},
    "Box11":            {"t": 0, "q": 1, "me": [2], "n": [3]},
    "BOX 12":           {"t": 0, "q": 1, "me": [], "n": [2]},
    "Box 13":           {"t": 0, "q": 1, "me": [], "n": [2]},
    "Box 14":           {"t": 0, "q": 1, "me": [2], "n": []},
    "Box15":            {"t": 0, "q": 1, "me": [], "n": [2]},
    "Box16":            {"t": 0, "q": 1, "me": [2], "e": [3], "n": [4, 5, 6, 7, 8, 9, 10, 11, 12]},
    "Box 17":           {"t": 0, "q": 1, "e": [2], "n": [3]},
    "Box18":            {"t": 0, "q": 1, "e": [2], "n": [3]},
    "Box19":            {"t": 0, "q": 1, "e": [2], "n": [3]},
    "Box20":            {"t": 0, "q": 1, "e": [2], "n": [3]},
    "BOX21":            {"t": 0, "q": 1, "e": [2], "n": [3]},
    "BOX22":            {"t": 0, "q": 1, "e": [2], "n": [3]},
    "BOX23":            {"t": 0, "q": 1, "e": [2], "n": [3, 9, 10, 11, 12]},
    "box24":            {"t": 0, "q": 1, "e": [2], "n": [3, 4, 5], "shifted": True},
    "BOX25":            {"t": 0, "q": 1, "me": [2, 3], "n": [4]},
    "Box 26":           {"t": 0, "q": 1, "me": [2], "n": [3]},
    "box27":            {"t": 0, "q": 1, "me": [], "n": [2]},
    "box28":            {"t": 0, "q": 1, "me": [], "n": []},
    "Box29":            {"t": 0, "q": 1, "me": [2], "n": [3, 4]},
    "Box30":            {"t": 0, "e": [1], "q": 2, "n": [3]},      # note: qty in col C
    "Box31":            {"t": None, "sundry_col": 0},
    "BOX32":            {"t": 0, "q": 1, "me": [], "n": []},
    "Loose in Own Box": {"t": 0, "q": 1, "me": [], "n": [2, 3]},
    "Box33":            {"t": 0, "q": 1, "me": [], "n": [2], "header": True},
    "Box 34":           {"t": 0, "q": 1, "me": [], "n": [2, 3], "header": True},
    "Box36":            {"t": 0, "q": 1, "me": [], "n": [], "header": True},
    "Box35":            {"t": 0, "q": 1, "me": [], "n": [2], "header": True},
}

BOX_NAMES = {  # sheet title -> tidy box id
    "Box 1 May 2022": "1", "Box 2 May 2022": "2", "Box 3 May 2022": "3",
    "Box4 May2022": "4", "Box 5 May2022": "5", "Box 6 May 2022": "6",
    "Box 7 May 2020": "7", "BOX8": "8", "Box9": "9", "Box 10": "10",
    "Box11": "11", "BOX 12": "12", "Box 13": "13", "Box 14": "14",
    "Box15": "15", "Box16": "16", "Box 17": "17", "Box18": "18",
    "Box19": "19", "Box20": "20", "BOX21": "21", "BOX22": "22",
    "BOX23": "23", "box24": "24", "BOX25": "25", "Box 26": "26",
    "box27": "27", "box28": "28", "Box29": "29", "Box30": "30",
    "Box31": "31", "BOX32": "32", "Box33": "33", "Box 34": "34",
    "Box35": "35", "Box36": "36", "Loose in Own Box": "Loose",
}

QTY_OVERRIDE = {("6", "ECL80"): 75}   # "50+" -> 75, per owner


def cell(v):
    if v is None:
        return ""
    return str(v).replace("\n", " ").strip()


def parse_qty(v):
    s = cell(v)
    if not s:
        return None
    s = s.replace("+", "").strip()
    try:
        return int(float(s))
    except ValueError:
        return None


def is_maker(s):
    return re.sub(r"[^A-Z]", "", s.upper()) in MAKERS


def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = V.init_db(DB)
    cur = con.cursor()
    today = datetime.date.today().isoformat()

    wb = openpyxl.load_workbook(SRC, data_only=True)
    types = {}          # type_key -> dict of accumulated info
    stock_rows = []
    sundries = []
    unresolved = []

    for ws in wb.worksheets:
        if ws.title not in LAYOUTS:
            continue
        lay = LAYOUTS[ws.title]
        boxid = BOX_NAMES[ws.title]
        last_key = None      # for continuation rows
        pending = {}         # box8-style: type -> accumulated single valves

        for ridx, row in enumerate(ws.iter_rows(values_only=True), 1):
            if not any(c not in (None, "") for c in row):
                continue
            if lay.get("skip_rows") and ridx in lay["skip_rows"]:
                continue

            def get(i):
                return cell(row[i]) if i < len(row) else ""

            # box24 has one row shifted right by a column
            offset = 0
            if lay.get("shifted") and not get(0) and get(1) and get(2):
                if parse_qty(row[2] if len(row) > 2 else None) is not None:
                    offset = 1

            if lay.get("sundry_col") is not None:
                sundries.append((boxid, get(lay["sundry_col"]), 1, None))
                continue

            tcol = lay["t"] + offset
            raw_type = get(tcol)

            if lay.get("header") and ridx == 1:
                continue
            if raw_type.upper() in ("VALVE", "BOX 1", ""):
                # continuation row: append any note text to the previous entry
                note_bits = [get(i + offset) for i in lay.get("n", [])]
                note_bits += [get(i + offset) for i in lay.get("me", [])]
                note_bits = [b for b in note_bits if b]
                if note_bits and last_key:
                    types.setdefault(last_key, {}).setdefault("extra", []).extend(note_bits)
                elif note_bits and not raw_type:
                    pass
                continue

            # non-valve items
            if any(h in raw_type.upper() for h in SUNDRY_HINTS):
                q = parse_qty(row[lay["q"] + offset]) if lay.get("q") is not None else 1
                sundries.append((boxid, raw_type, q or 1, get(lay.get("n", [99])[0]) if lay.get("n") else None))
                continue

            key = V.norm(raw_type)
            if not key:
                continue

            # quantity
            qty = None
            if lay.get("qty_or_maker") is not None:
                q = parse_qty(row[lay["qty_or_maker"]])
                qty = q if q is not None else 1
            elif lay.get("q") is not None:
                qty = parse_qty(row[lay["q"] + offset] if lay["q"] + offset < len(row) else None)
            if qty is None:
                qty = 1
            if (boxid, key) in QTY_OVERRIDE:
                qty = QTY_OVERRIDE[(boxid, key)]

            # manufacturer vs equivalents
            maker, equivs = None, []
            for i in lay.get("me", []):
                s = get(i + offset)
                if not s:
                    continue
                if is_maker(s) and maker is None:
                    maker = s
                else:
                    equivs.append(s)
            for i in lay.get("e", []):
                s = get(i + offset)
                if s:
                    equivs.append(s)

            notes = " ".join(x for x in (get(i + offset) for i in lay.get("n", [])) if x)

            # condition hints
            cond = None
            up = (notes + " " + " ".join(equivs)).upper()
            for c in ("MATCHED QUAD", "MATCHED PAIR", "NOS", "LOOSE BASE",
                      "WITH BASE", "WITHBASE", "UNMARKED", "PULLS"):
                if c in up:
                    cond = c.title()
                    break

            if raw_type.strip().startswith("?") or "UNIDENTIF" in notes.upper():
                unresolved.append((boxid, raw_type, notes))

            stock_rows.append({
                "type_key": key, "box": boxid, "qty": qty,
                "manufacturer": maker, "condition": cond,
                "notes": notes or None,
            })

            t = types.setdefault(key, {"name": raw_type.strip(), "equivs": set(), "desc": []})
            for e in equivs:
                e = e.strip()
                if is_maker(e) or len(e) < 2 or e.upper().startswith("AS ABOVE"):
                    continue
                if not re.search(r"[A-Za-z0-9]{2}", e):
                    continue
                t["equivs"].add(e)
            if notes and len(notes) > 25:
                t["desc"].append(notes)
            last_key = key

    # ---- consolidate identical lots in the same box (e.g. Box 8 KT66) ----
    merged = {}
    for r in stock_rows:
        k = (r["type_key"], r["box"], r["manufacturer"], r["condition"])
        if k in merged:
            merged[k]["qty"] += r["qty"]
            if r["notes"] and r["notes"] not in (merged[k]["notes"] or ""):
                merged[k]["notes"] = " / ".join(filter(None, [merged[k]["notes"], r["notes"]]))
        else:
            merged[k] = dict(r)
    stock_rows = list(merged.values())

    # ---- write valve_type ----
    for key, t in sorted(types.items()):
        inf = V.classify(t["name"])
        desc = max(t["desc"], key=len) if t["desc"] else None
        extra = " | ".join(t.get("extra", []))[:4000] or None
        cur.execute("""
            INSERT INTO valve_type
              (type_key, name, function, family, heater_v, heater_a,
               typical_use, equivalents, confidence, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (key, t["name"].strip().upper(), inf.get("function"), inf.get("family"),
             inf.get("heater_v"), inf.get("heater_a"), desc,
             " ".join(sorted(t["equivs"])) or None,
             "inferred", extra))

    # ---- write stock ----
    for r in stock_rows:
        cur.execute("""INSERT INTO stock
              (type_key, box, qty, manufacturer, condition, date_added, notes)
              VALUES (?,?,?,?,?,?,?)""",
            (r["type_key"], r["box"], r["qty"], r["manufacturer"],
             r["condition"], today, r["notes"]))

    for b, d, q, n in sundries:
        cur.execute("INSERT INTO sundry (box, description, qty, notes) VALUES (?,?,?,?)",
                    (b, d, q, n))

    for boxid in sorted(set(BOX_NAMES.values())):
        cur.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                    (boxid, "attic"))

    con.commit()

    n_types = cur.execute("SELECT COUNT(*) FROM valve_type").fetchone()[0]
    n_lots = cur.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
    n_valves = cur.execute("SELECT SUM(qty) FROM stock").fetchone()[0]
    n_sundry = cur.execute("SELECT COUNT(*) FROM sundry").fetchone()[0]
    print(f"types      : {n_types}")
    print(f"stock lots : {n_lots}")
    print(f"valves     : {n_valves}")
    print(f"sundries   : {n_sundry}")
    if unresolved:
        print(f"\nneeds a look ({len(unresolved)}):")
        for b, t, n in unresolved:
            print(f"  box {b}: {t}  {n[:60]}")
    con.close()


if __name__ == "__main__":
    main()
