#!/usr/bin/env python3
"""
snapshot.py - write a diffable text snapshot of the database into data/.

The .db file is binary: git can store it but not diff it, and every edit
rewrites the whole blob. So the database itself is gitignored and this writes
the same content as text that version control can actually show you changes in.

  python3 snapshot.py                 # refresh data/ from valves.db
  python3 snapshot.py --restore       # rebuild valves.db from data/valves.sql
  python3 snapshot.py --strip-notes   # omit third-party descriptive text

Run it before committing. `--restore` is what someone does after cloning.
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

DATA = "data"

TYPE_COLS = ["type_key", "name", "function", "family", "base", "pins",
             "heater_v", "heater_a", "va_max", "pa_max", "gm", "mu",
             "power_out", "freq_max", "typical_use", "equivalents",
             "datasheet_path", "datasheet_url", "confidence", "notes"]
STOCK_COLS = ["id", "type_key", "box", "qty", "manufacturer", "condition",
              "date_added", "notes"]
SOCKET_COLS = ["id", "base", "box", "qty", "condition", "notes"]
DOCUMENT_COLS = ["id", "type_key", "title", "abstract", "path", "url", "added"]


def write_csv(con, path, table, cols, strip=()):
    """Dump `cols` from `table` (ordered by the first column) to a CSV at `path`.

    `strip` names columns whose values are blanked out instead of written -
    used to omit third-party descriptive text (e.g. typical_use, notes)
    before the repo goes public.
    """
    rows = con.execute(f"SELECT {','.join(cols)} FROM {table} ORDER BY {cols[0]}")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            out = []
            for c, v in zip(cols, r):
                out.append("" if (v is None or c in strip) else v)
            w.writerow(out)


def snapshot(args):
    """Export the database at args.db to data/*.csv plus a full data/valves.sql dump.

    Writes one CSV per table (types, stock, sundry, sockets, documents) and a SQL dump
    that `restore()` can replay to recreate the database from scratch. When
    args.strip_notes is set, the typical_use and notes columns are blanked
    in the CSV exports (the SQL dump always has the full data).
    """
    con = V.connect(args.db)
    os.makedirs(DATA, exist_ok=True)
    strip = ("typical_use", "notes") if args.strip_notes else ()

    write_csv(con, f"{DATA}/types.csv", "valve_type", TYPE_COLS, strip)
    write_csv(con, f"{DATA}/stock.csv", "stock", STOCK_COLS,
              ("notes",) if args.strip_notes else ())
    write_csv(con, f"{DATA}/sundry.csv", "sundry",
              ["id", "box", "description", "qty", "notes"])
    write_csv(con, f"{DATA}/sockets.csv", "socket", SOCKET_COLS)
    write_csv(con, f"{DATA}/documents.csv", "document", DOCUMENT_COLS)

    # Full SQL dump, so a clone can rebuild the database exactly.
    with open(f"{DATA}/valves.sql", "w", encoding="utf-8") as f:
        for line in con.iterdump():
            f.write(line + "\n")

    n = con.execute("SELECT COUNT(*) FROM valve_type").fetchone()[0]
    m = con.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
    q = con.execute("SELECT SUM(qty) FROM stock").fetchone()[0]
    print(f"snapshot written to {DATA}/  -  {n} types, {m} lots, {q} valves"
          + ("  (notes stripped)" if args.strip_notes else ""))


def restore(args):
    """Rebuild args.db from data/valves.sql, refusing to clobber an existing db unless --force.

    This is what a fresh clone runs to get a working valves.db, since the
    binary database itself is gitignored.
    """
    import sqlite3
    if os.path.exists(args.db) and not args.force:
        print(f"{args.db} already exists - use --force to overwrite")
        return
    if os.path.exists(args.db):
        os.remove(args.db)
    # Foreign keys must be off while loading: a SQL dump lists tables
    # alphabetically, so stock rows arrive before valve_type exists.
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys = OFF")
    with open(f"{DATA}/valves.sql", encoding="utf-8") as f:
        con.executescript(f.read())
    con.commit()
    bad = con.execute("PRAGMA foreign_key_check").fetchall()
    n = con.execute("SELECT SUM(qty) FROM stock").fetchone()[0]
    con.close()
    print(f"rebuilt {args.db} from {DATA}/valves.sql  -  {n} valves")
    if bad:
        print(f"warning: {len(bad)} rows fail foreign key checks")


def main():
    """Parse CLI args and dispatch to restore() or snapshot() (the default)."""
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=V.DB_DEFAULT)
    p.add_argument("--restore", action="store_true", help="rebuild the .db from data/")
    p.add_argument("--force", action="store_true", help="overwrite an existing .db on restore")
    p.add_argument("--strip-notes", action="store_true",
                   help="omit typical_use and notes from the CSV exports")
    a = p.parse_args()
    restore(a) if a.restore else snapshot(a)


if __name__ == "__main__":
    main()
