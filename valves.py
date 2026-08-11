#!/usr/bin/env python3
"""
valves.py - valve stock inventory.

  valves.py box 12                  what is in box 12
  valves.py find KT66               which boxes hold KT66 (follows equivalents)
  valves.py search --function pentode --heater 6.3 --pa '>20'
  valves.py add EL34 --box 1 --qty 4 --maker Svetlana
  valves.py take EL34 --box 1 --qty 2
  valves.py show ECC83              full reference record
  valves.py set ECC83 --pa 1.2 --mu 100 --base B9A --confirm
  valves.py sheet ECC83             open the local datasheet
  valves.py scan                    link archive PDFs to types
  valves.py gaps                    types with no datasheet / no parameters
  valves.py export inventory.xlsx
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V


# ---------------------------------------------------------------- helpers

def resolve(con, name):
    """Find a type_key from user input, following equivalents and substrings."""
    key = V.norm(name)
    if not key:
        return []
    r = con.execute("SELECT type_key FROM valve_type WHERE type_key=?", (key,)).fetchone()
    if r:
        return [r["type_key"]]
    hits = [x["type_key"] for x in con.execute(
        "SELECT type_key FROM valve_type WHERE type_key LIKE ?", (f"%{key}%",))]
    if hits:
        return hits
    # search the equivalents lists
    return [x["type_key"] for x in con.execute(
        "SELECT type_key FROM valve_type WHERE UPPER(REPLACE(equivalents,' ','')) LIKE ?",
        (f"%{key}%",))]


def table(rows, cols):
    if not rows:
        print("  (nothing)")
        return
    w = {c: max(len(c), max(len(str(r[c] if r[c] is not None else "")) for r in rows)) for c in cols}
    w = {c: min(v, 46) for c, v in w.items()}
    print("  " + "  ".join(c.upper().ljust(w[c]) for c in cols))
    print("  " + "  ".join("-" * w[c] for c in cols))
    for r in rows:
        cells = []
        for c in cols:
            s = "" if r[c] is None else str(r[c])
            s = s if len(s) <= w[c] else s[:w[c] - 1] + "…"
            cells.append(s.ljust(w[c]))
        print("  " + "  ".join(cells))


def parse_cmp(expr):
    """'>20' -> ('>', 20.0);  '6.3' -> ('=', 6.3)"""
    m = re.match(r"^\s*(>=|<=|>|<|=)?\s*([\d.]+)\s*$", str(expr))
    if not m:
        raise ValueError(f"cannot parse comparison: {expr}")
    return (m.group(1) or "="), float(m.group(2))


# ---------------------------------------------------------------- commands

def cmd_box(con, a):
    rows = [dict(r) for r in con.execute(
        "SELECT type, qty, manufacturer, condition, function, notes "
        "FROM v_stock WHERE box=? COLLATE NOCASE ORDER BY type", (a.box,))]
    total = sum(r["qty"] for r in rows)
    print(f"\nBox {a.box} - {len(rows)} lots, {total} valves\n")
    table(rows, ["type", "qty", "manufacturer", "condition", "function"])
    sund = [dict(r) for r in con.execute(
        "SELECT description, qty FROM sundry WHERE box=? COLLATE NOCASE", (a.box,))]
    if sund:
        print("\n  other items:")
        table(sund, ["description", "qty"])
    bases = [dict(r) for r in con.execute(
        "SELECT base, qty, condition, notes FROM socket WHERE box=? COLLATE NOCASE", (a.box,))]
    if bases:
        print("\n  bases/sockets:")
        table(bases, ["base", "qty", "condition", "notes"])
    print()


def cmd_find(con, a):
    keys = resolve(con, a.type)
    if not keys:
        print(f"no type matching '{a.type}'")
        return
    for k in keys:
        t = con.execute("SELECT * FROM valve_type WHERE type_key=?", (k,)).fetchone()
        rows = [dict(r) for r in con.execute(
            "SELECT box, qty, manufacturer, condition, notes FROM v_stock "
            "WHERE type_key=? ORDER BY CAST(box AS INTEGER), box", (k,))]
        total = sum(r["qty"] for r in rows)
        print(f"\n{t['name']}  -  {total} in stock across {len(rows)} box(es)")
        if t["function"]:
            print(f"  {t['function']}"
                  + (f", heater {t['heater_v']}V" if t["heater_v"] else "")
                  + (f", heater {t['heater_a']}A" if t["heater_a"] else ""))
        if t["equivalents"]:
            print(f"  equivalents: {t['equivalents']}")
        print()
        table(rows, ["box", "qty", "manufacturer", "condition"])
    print()


def cmd_show(con, a):
    keys = resolve(con, a.type)
    if not keys:
        print(f"no type matching '{a.type}'")
        return
    t = con.execute("SELECT * FROM valve_type WHERE type_key=?", (keys[0],)).fetchone()
    print(f"\n{t['name']}   [{t['confidence']}]")
    print("=" * (len(t["name"]) + 16))
    fields = [("function", ""), ("family", ""), ("base", ""), ("pins", ""),
              ("heater_v", " V"), ("heater_a", " A"), ("va_max", " V"),
              ("pa_max", " W"), ("gm", " mA/V"), ("mu", ""),
              ("power_out", " W"), ("freq_max", " MHz")]
    for f, unit in fields:
        if t[f] is not None:
            print(f"  {f:<14} {t[f]}{unit}")
    if t["equivalents"]:
        print(f"  {'equivalents':<14} {t['equivalents']}")
    if t["datasheet_path"]:
        print(f"  {'datasheet':<14} {t['datasheet_path']}")
    if t["typical_use"]:
        print(f"\n  {t['typical_use']}")
    if t["notes"]:
        print(f"\n  notes: {t['notes'][:1500]}")
    rows = [dict(r) for r in con.execute(
        "SELECT box, qty, manufacturer, condition FROM v_stock WHERE type_key=?", (keys[0],))]
    print(f"\n  stock ({sum(r['qty'] for r in rows)}):")
    table(rows, ["box", "qty", "manufacturer", "condition"])
    print()


def cmd_search(con, a):
    where, args = ["1=1"], []
    if a.function:
        where.append("(LOWER(t.function) LIKE ? OR LOWER(t.typical_use) LIKE ?)")
        args += [f"%{a.function.lower()}%"] * 2
    if a.maker:
        where.append("LOWER(s.manufacturer) LIKE ?")
        args.append(f"%{a.maker.lower()}%")
    if a.box:
        where.append("s.box = ? COLLATE NOCASE")
        args.append(a.box)
    for field, expr in (("t.heater_v", a.heater), ("t.pa_max", a.pa),
                        ("t.va_max", a.va), ("t.freq_max", a.freq),
                        ("t.gm", a.gm), ("t.mu", a.mu)):
        if expr:
            op, val = parse_cmp(expr)
            where.append(f"{field} {op} ?")
            args.append(val)
    if a.text:
        where.append("(LOWER(t.name) LIKE ? OR LOWER(t.typical_use) LIKE ? "
                     "OR LOWER(t.notes) LIKE ? OR LOWER(t.equivalents) LIKE ?)")
        args += [f"%{a.text.lower()}%"] * 4

    sql = f"""SELECT t.name AS type, s.box, s.qty, s.manufacturer,
                     t.function, t.heater_v, t.pa_max
              FROM stock s JOIN valve_type t ON s.type_key=t.type_key
              WHERE {' AND '.join(where)}
              ORDER BY t.name, CAST(s.box AS INTEGER)"""
    rows = [dict(r) for r in con.execute(sql, args)]
    print(f"\n{len(rows)} lots, {sum(r['qty'] for r in rows)} valves\n")
    table(rows, ["type", "box", "qty", "manufacturer", "function", "heater_v", "pa_max"])
    print()


def cmd_add(con, a):
    key = V.norm(a.type)
    exists = con.execute("SELECT 1 FROM valve_type WHERE type_key=?", (key,)).fetchone()
    if not exists:
        inf = V.classify(a.type)
        con.execute("""INSERT INTO valve_type (type_key,name,function,family,
                       heater_v,heater_a,confidence) VALUES (?,?,?,?,?,?,'inferred')""",
                    (key, a.type.strip(), inf.get("function"), inf.get("family"),
                     inf.get("heater_v"), inf.get("heater_a")))
        print(f"new type created: {a.type}"
              + (f"  ({inf.get('function')})" if inf.get("function") else ""))
    con.execute("""INSERT INTO stock (type_key,box,qty,manufacturer,condition,date_added,notes)
                   VALUES (?,?,?,?,?,?,?)""",
                (key, a.box, a.qty, a.maker, a.condition,
                 datetime.date.today().isoformat(), a.notes))
    con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)", (a.box, "attic"))
    con.commit()
    print(f"added {a.qty} x {a.type} to box {a.box}")


def cmd_take(con, a):
    keys = resolve(con, a.type)
    if not keys:
        print("no such type")
        return
    rows = list(con.execute(
        "SELECT id,box,qty FROM stock WHERE type_key=?"
        + (" AND box=? COLLATE NOCASE" if a.box else "") + " ORDER BY qty DESC",
        (keys[0], a.box) if a.box else (keys[0],)))
    if not rows:
        print("none in stock")
        return
    left = a.qty
    for r in rows:
        if left <= 0:
            break
        take = min(left, r["qty"])
        if take == r["qty"]:
            con.execute("DELETE FROM stock WHERE id=?", (r["id"],))
        else:
            con.execute("UPDATE stock SET qty=qty-? WHERE id=?", (take, r["id"]))
        print(f"  took {take} from box {r['box']}")
        left -= take
    if left:
        print(f"  short by {left}")
    con.commit()


def cmd_move(con, a):
    keys = resolve(con, a.type)
    con.execute("UPDATE stock SET box=? WHERE type_key=? AND box=? COLLATE NOCASE",
                (a.to, keys[0], a.frm))
    con.commit()
    print(f"moved {keys[0]} from box {a.frm} to box {a.to}")


# ---------------------------------------------------------------- bases/sockets

def cmd_bases(con, a):
    where, args = ["1=1"], []
    if a.base:
        where.append("LOWER(base) LIKE ?")
        args.append(f"%{a.base.lower()}%")
    if a.box:
        where.append("box = ? COLLATE NOCASE")
        args.append(a.box)
    rows = [dict(r) for r in con.execute(
        f"SELECT base, box, qty, condition, notes FROM socket WHERE {' AND '.join(where)} "
        "ORDER BY base, CAST(box AS INTEGER), box", args)]
    total = sum(r["qty"] for r in rows)
    print(f"\n{len(rows)} lots, {total} sockets/bases\n")
    table(rows, ["base", "box", "qty", "condition", "notes"])
    print()


def cmd_sock_add(con, a):
    con.execute("INSERT INTO socket (base,box,qty,condition,notes) VALUES (?,?,?,?,?)",
                (a.base.strip(), a.box, a.qty, a.condition, a.notes))
    con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)", (a.box, "attic"))
    con.commit()
    print(f"added {a.qty} x {a.base} to box {a.box}")


def cmd_sock_take(con, a):
    rows = list(con.execute(
        "SELECT id,box,qty FROM socket WHERE LOWER(base)=?"
        + (" AND box=? COLLATE NOCASE" if a.box else "") + " ORDER BY qty DESC",
        (a.base.lower(), a.box) if a.box else (a.base.lower(),)))
    if not rows:
        print("none in stock")
        return
    left = a.qty
    for r in rows:
        if left <= 0:
            break
        take = min(left, r["qty"])
        if take == r["qty"]:
            con.execute("DELETE FROM socket WHERE id=?", (r["id"],))
        else:
            con.execute("UPDATE socket SET qty=qty-? WHERE id=?", (take, r["id"]))
        print(f"  took {take} from box {r['box']}")
        left -= take
    if left:
        print(f"  short by {left}")
    con.commit()


def cmd_sock_move(con, a):
    con.execute("UPDATE socket SET box=? WHERE LOWER(base)=? AND box=? COLLATE NOCASE",
                (a.to, a.base.lower(), a.frm))
    con.commit()
    print(f"moved {a.base} from box {a.frm} to box {a.to}")


def cmd_set(con, a):
    keys = resolve(con, a.type)
    if not keys:
        print("no such type")
        return
    fields, args = [], []
    for name in ("function", "base", "pins", "heater_v", "heater_a", "va_max",
                 "pa_max", "gm", "mu", "power_out", "freq_max", "typical_use",
                 "equivalents", "datasheet_path", "datasheet_url", "notes"):
        val = getattr(a, name, None)
        if val is not None:
            fields.append(f"{name}=?")
            args.append(val)
    if a.confirm:
        fields.append("confidence='confirmed'")
    if not fields:
        print("nothing to set")
        return
    args.append(keys[0])
    con.execute(f"UPDATE valve_type SET {','.join(fields)} WHERE type_key=?", args)
    con.commit()
    print(f"updated {keys[0]}")


def cmd_merge(con, a):
    """Fold one type into another, e.g. ECC83S -> ECC83, keeping all stock."""
    src, dst = V.norm(a.source), V.norm(a.into)
    s = con.execute("SELECT * FROM valve_type WHERE type_key=?", (src,)).fetchone()
    d = con.execute("SELECT * FROM valve_type WHERE type_key=?", (dst,)).fetchone()
    if not s or not d:
        print("both types must already exist")
        return
    n = con.execute("SELECT COALESCE(SUM(qty),0) c FROM stock WHERE type_key=?", (src,)).fetchone()["c"]
    if not a.yes:
        print(f"would move {n} valves from {s['name']} into {d['name']}, "
              f"recording '{s['name']}' as an equivalent. re-run with --yes")
        return
    eq = " ".join(sorted(set((d["equivalents"] or "").split()) | {s["name"]}))
    con.execute("UPDATE valve_type SET equivalents=? WHERE type_key=?", (eq, dst))
    con.execute("UPDATE stock SET type_key=?, notes=COALESCE(notes||' ','')||? "
                "WHERE type_key=?", (dst, f"[was listed as {s['name']}]", src))
    con.execute("DELETE FROM valve_type WHERE type_key=?", (src,))
    con.commit()
    print(f"merged {s['name']} into {d['name']} ({n} valves)")


def cmd_dupes(con, a):
    """Suggest types that look like variants of each other."""
    rows = list(con.execute("SELECT type_key, name FROM valve_type ORDER BY type_key"))
    keys = [r["type_key"] for r in rows]
    out = []
    for i, k in enumerate(keys):
        for k2 in keys[i + 1:]:
            if k2.startswith(k) and len(k2) - len(k) <= 2 and len(k) >= 3:
                out.append({"type": k, "variant": k2})
            elif k.startswith(k2) and len(k) - len(k2) <= 2 and len(k2) >= 3:
                out.append({"type": k2, "variant": k})
    print(f"\n{len(out)} possible duplicate pairs - review, then use 'merge':\n")
    table(out, ["type", "variant"])
    print()


def cmd_scan(con, a):
    """Walk the local datasheet archive and attach files to types."""
    root = a.archive
    if not os.path.isdir(root):
        print(f"archive directory not found: {root}")
        return
    index = {}
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if not f.lower().endswith((".pdf", ".png", ".gif", ".jpg")):
                continue
            stem = V.norm(os.path.splitext(f)[0].split("~")[0])
            if stem:
                index.setdefault(stem, os.path.relpath(os.path.join(dirpath, f), root))
    n = 0
    for r in con.execute("SELECT type_key FROM valve_type WHERE datasheet_path IS NULL"):
        p = index.get(r["type_key"])
        if p:
            con.execute("UPDATE valve_type SET datasheet_path=? WHERE type_key=?",
                        (p, r["type_key"]))
            n += 1
    con.commit()
    print(f"archive files indexed: {len(index)}")
    print(f"types newly linked   : {n}")
    miss = con.execute("SELECT COUNT(*) c FROM valve_type WHERE datasheet_path IS NULL").fetchone()["c"]
    print(f"types still unlinked : {miss}")


def cmd_sheet(con, a):
    keys = resolve(con, a.type)
    if not keys:
        print("no such type")
        return
    t = con.execute("SELECT name,datasheet_path FROM valve_type WHERE type_key=?", (keys[0],)).fetchone()
    if not t["datasheet_path"]:
        print(f"no local datasheet for {t['name']}")
        print(f"  try: https://frank.pocnet.net/sheets/  or  https://tdsl.duncanamps.com/show.php?des={t['name']}")
        return
    path = os.path.join(a.archive, t["datasheet_path"])
    print(path)
    if a.open:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, path], check=False)


def cmd_gaps(con, a):
    print("\ntypes held in stock with no datasheet linked:")
    rows = [dict(r) for r in con.execute("""
        SELECT t.name AS type, SUM(s.qty) qty, t.function
        FROM valve_type t JOIN stock s ON s.type_key=t.type_key
        WHERE t.datasheet_path IS NULL
        GROUP BY t.type_key ORDER BY qty DESC LIMIT ?""", (a.limit,))]
    table(rows, ["type", "qty", "function"])
    print("\ntypes with no function classified:")
    rows = [dict(r) for r in con.execute("""
        SELECT t.name AS type, SUM(s.qty) qty FROM valve_type t
        JOIN stock s ON s.type_key=t.type_key
        WHERE t.function IS NULL GROUP BY t.type_key ORDER BY qty DESC LIMIT ?""",
        (a.limit,))]
    table(rows, ["type", "qty"])
    print()


def cmd_stats(con, a):
    q = lambda s: con.execute(s).fetchone()[0]
    print(f"\n  types            {q('SELECT COUNT(*) FROM valve_type')}")
    print(f"  stock lots       {q('SELECT COUNT(*) FROM stock')}")
    print(f"  valves total     {q('SELECT SUM(qty) FROM stock')}")
    print(f"  boxes in use     {q('SELECT COUNT(DISTINCT box) FROM stock')}")
    print(f"  datasheets held  {q('SELECT COUNT(*) FROM valve_type WHERE datasheet_path IS NOT NULL')}")
    print(f"""  confirmed params {q("SELECT COUNT(*) FROM valve_type WHERE confidence='confirmed'")}""")
    print(f"  bases/sockets    {q('SELECT COALESCE(SUM(qty),0) FROM socket')}")
    print("\n  by function:")
    rows = [dict(r) for r in con.execute("""
        SELECT COALESCE(t.function,'(unclassified)') AS function,
               COUNT(DISTINCT t.type_key) types, SUM(s.qty) valves
        FROM valve_type t JOIN stock s ON s.type_key=t.type_key
        GROUP BY 1 ORDER BY valves DESC LIMIT 20""")]
    table(rows, ["function", "types", "valves"])
    print("\n  fullest boxes:")
    rows = [dict(r) for r in con.execute("""
        SELECT box, COUNT(*) lots, SUM(qty) valves FROM stock
        GROUP BY box ORDER BY valves DESC LIMIT 10""")]
    table(rows, ["box", "lots", "valves"])
    print()


def cmd_export(con, a):
    import openpyxl
    from openpyxl.styles import Font, Alignment
    wb = openpyxl.Workbook()

    ws = wb.active
    ws.title = "Stock"
    cols = ["Box", "Type", "Qty", "Manufacturer", "Condition", "Function",
            "Heater V", "Pa max W", "Datasheet", "Notes"]
    ws.append(cols)
    for r in con.execute("""SELECT s.box, COALESCE(t.name,s.type_key), s.qty,
                                   s.manufacturer, s.condition, t.function,
                                   t.heater_v, t.pa_max, t.datasheet_path, s.notes
                            FROM stock s LEFT JOIN valve_type t ON s.type_key=t.type_key
                            ORDER BY CAST(s.box AS INTEGER), s.box, t.name"""):
        ws.append([(x[:300] if isinstance(x, str) else x) for x in r])

    ws2 = wb.create_sheet("Types")
    tcols = ["Type", "Function", "Family", "Base", "Heater V", "Heater A",
             "Va max", "Pa max W", "gm mA/V", "mu", "Power out W", "Freq max MHz",
             "Equivalents", "Datasheet", "Confidence", "In stock"]
    ws2.append(tcols)
    for r in con.execute("""SELECT t.name,t.function,t.family,t.base,t.heater_v,t.heater_a,
                                   t.va_max,t.pa_max,t.gm,t.mu,t.power_out,t.freq_max,
                                   t.equivalents,t.datasheet_path,t.confidence,
                                   (SELECT SUM(qty) FROM stock WHERE type_key=t.type_key)
                            FROM valve_type t ORDER BY t.name"""):
        ws2.append([(x[:300] if isinstance(x, str) else x) for x in r])

    ws3 = wb.create_sheet("Other items")
    ws3.append(["Box", "Description", "Qty", "Notes"])
    for r in con.execute("SELECT box, description, qty, notes FROM sundry"):
        ws3.append(list(r))

    for sh in wb.worksheets:
        for c in sh[1]:
            c.font = Font(name="Arial", bold=True)
            c.alignment = Alignment(horizontal="left")
        sh.freeze_panes = "A2"
        sh.auto_filter.ref = sh.dimensions
        for col in sh.columns:
            letter = col[0].column_letter
            width = max(len(str(c.value)) if c.value else 0 for c in col[:400])
            sh.column_dimensions[letter].width = min(max(width + 2, 9), 44)
        for row in sh.iter_rows(min_row=2):
            for c in row:
                c.font = Font(name="Arial")
    wb.save(a.path)
    print(f"written: {a.path}")


# ---------------------------------------------------------------- cli

def main():
    # Let output be piped into head/less without a BrokenPipeError traceback.
    try:
        from signal import signal, SIGPIPE, SIG_DFL
        signal(SIGPIPE, SIG_DFL)
    except (ImportError, ValueError):
        pass  # not available on Windows

    # Notes carry scraped text with non-Latin scripts (Cyrillic type names,
    # mu signs); Windows consoles default stdout to cp1252, which can't
    # encode them and crashes the print. UTF-8 with replacement is safe
    # everywhere and matches the DB's own encoding.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # e.g. stdout replaced by something without reconfigure

    p = argparse.ArgumentParser(description="valve stock inventory")
    p.add_argument("--db", default=V.DB_DEFAULT)
    p.add_argument("--archive", default=V.ARCHIVE_DEFAULT)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("box", help="list a box's contents");  s.add_argument("box");  s.set_defaults(fn=cmd_box)
    s = sub.add_parser("find", help="which boxes hold a type"); s.add_argument("type"); s.set_defaults(fn=cmd_find)
    s = sub.add_parser("show", help="full reference record");  s.add_argument("type"); s.set_defaults(fn=cmd_show)

    s = sub.add_parser("search", help="filter by parameters")
    s.add_argument("--function"); s.add_argument("--maker"); s.add_argument("--box")
    s.add_argument("--heater", help="e.g. 6.3 or '<7'")
    s.add_argument("--pa", help="anode dissipation, e.g. '>20'")
    s.add_argument("--va"); s.add_argument("--freq"); s.add_argument("--gm"); s.add_argument("--mu")
    s.add_argument("--text", help="free text over name, use, notes, equivalents")
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("add", help="add stock")
    s.add_argument("type"); s.add_argument("--box", required=True)
    s.add_argument("--qty", type=int, default=1); s.add_argument("--maker")
    s.add_argument("--condition"); s.add_argument("--notes")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("take", help="remove stock you have used")
    s.add_argument("type"); s.add_argument("--qty", type=int, default=1)
    s.add_argument("--box"); s.set_defaults(fn=cmd_take)

    s = sub.add_parser("move", help="move a type between boxes")
    s.add_argument("type"); s.add_argument("--frm", required=True)
    s.add_argument("--to", required=True); s.set_defaults(fn=cmd_move)

    s = sub.add_parser("bases", help="list valve base/socket stock")
    s.add_argument("--base"); s.add_argument("--box"); s.set_defaults(fn=cmd_bases)

    s = sub.add_parser("sock-add", help="add base/socket stock")
    s.add_argument("base"); s.add_argument("--box", required=True)
    s.add_argument("--qty", type=int, default=1)
    s.add_argument("--condition"); s.add_argument("--notes")
    s.set_defaults(fn=cmd_sock_add)

    s = sub.add_parser("sock-take", help="remove base/socket stock")
    s.add_argument("base"); s.add_argument("--qty", type=int, default=1)
    s.add_argument("--box"); s.set_defaults(fn=cmd_sock_take)

    s = sub.add_parser("sock-move", help="move base/socket stock between boxes")
    s.add_argument("base"); s.add_argument("--frm", required=True)
    s.add_argument("--to", required=True); s.set_defaults(fn=cmd_sock_move)

    s = sub.add_parser("set", help="edit a type's reference parameters")
    s.add_argument("type")
    for f in ("function", "base", "typical_use", "equivalents",
              "datasheet_path", "datasheet_url", "notes"):
        s.add_argument("--" + f.replace("_", "-"), dest=f)
    for f in ("heater_v", "heater_a", "va_max", "pa_max", "gm", "mu",
              "power_out", "freq_max"):
        s.add_argument("--" + f.replace("_", "-").replace("-max", ""), dest=f, type=float)
    s.add_argument("--pins", type=int)
    s.add_argument("--confirm", action="store_true", help="mark as read from a datasheet")
    s.set_defaults(fn=cmd_set)

    s = sub.add_parser("merge", help="fold one type into another")
    s.add_argument("source"); s.add_argument("into")
    s.add_argument("--yes", action="store_true"); s.set_defaults(fn=cmd_merge)
    s = sub.add_parser("dupes", help="list possible duplicate type entries"); s.set_defaults(fn=cmd_dupes)

    s = sub.add_parser("scan", help="link local archive files to types"); s.set_defaults(fn=cmd_scan)
    s = sub.add_parser("sheet", help="locate a datasheet")
    s.add_argument("type"); s.add_argument("--open", action="store_true"); s.set_defaults(fn=cmd_sheet)
    s = sub.add_parser("gaps", help="what still needs data")
    s.add_argument("--limit", type=int, default=25); s.set_defaults(fn=cmd_gaps)
    s = sub.add_parser("stats", help="collection summary"); s.set_defaults(fn=cmd_stats)
    s = sub.add_parser("export", help="write an xlsx snapshot")
    s.add_argument("path", nargs="?", default="valve_inventory.xlsx"); s.set_defaults(fn=cmd_export)

    a = p.parse_args()
    con = V.init_db(a.db)
    a.fn(con, a)
    con.close()


if __name__ == "__main__":
    main()
