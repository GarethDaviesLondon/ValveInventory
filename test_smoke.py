#!/usr/bin/env python3
"""
test_smoke.py - fast checks that the pieces still fit together.

Run with:  python3 test_smoke.py
No test framework needed (no pytest/unittest) - just a flat script of
check()/check_true() calls run top to bottom, all failures collected and
reported together at the end, non-zero exit if any failed. Covers, in
order: type-name normalisation (norm()), the naming-convention classifier
(classify()), a database round-trip through a scratch SQLite file
(schema + insert + the v_stock view), an in-place migration of a database
built to the pre-1.4 schema, every CLI subcommand run as a real subprocess
against that scratch database, and (if data/ is present) the snapshot
restore path. Deliberately does not touch the real valves.db -
every check that needs a database uses a fresh file under tempfile.mkdtemp().
"""

import os
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

failures = []


def check(label, got, want):
    """Record a failure (for the final report) if got != want."""
    if got != want:
        failures.append(f"{label}: got {got!r}, wanted {want!r}")


def check_true(label, cond):
    """Record a failure (for the final report) if cond is falsy."""
    if not cond:
        failures.append(label)


# ---- normalisation -------------------------------------------------------
check("norm strips service prefix", V.norm("jan 7289"), "7289")
check("norm strips punctuation", V.norm("PY 4-400"), "PY4400")
check("norm uppercases", V.norm("ecc83s"), "ECC83S")
check("norm handles None", V.norm(None), None)

# ---- classifier ----------------------------------------------------------
c = V.classify("ECC83")
check("ECC83 function", c.get("function"), "double triode")
check("ECC83 heater", c.get("heater_v"), 6.3)

check("EL34 is an output valve", V.classify("EL34")["function"], "output pentode/tetrode")
check("KT66 beats the European code", V.classify("KT66")["heater_v"], 6.3)
check("30PL14 is a series-chain type", V.classify("30PL14").get("heater_a"), 0.3)
check("6AU6 reads as American", V.classify("6AU6")["heater_v"], 6.3)

# The electrode-count heuristic used to mislabel these; both are curated now.
check("6X4 is a rectifier", V.classify("6X4")["function"], "full-wave rectifier")
check("6SN7 is a double triode", V.classify("6SN7")["function"], "double triode")

# 8D3 is a British service code for the EF91; it is in the curated table
# precisely because no naming rule would get it right.
check("8D3 comes from the curated table", V.classify("8D3")["function"], "RF pentode")

# Ambiguous codes should stay blank rather than be guessed wrongly. 12AX7 gets
# a heater voltage from the RETMA number but no function, because the trailing
# digit is an electrode count and does not imply one.
check_true("207 is left unclassified", V.classify("207") == {})
check_true("12AX7 gets no guessed function", "function" not in V.classify("12AX7"))
check("12AX7 still gets its heater", V.classify("12AX7")["heater_v"], 12.6)

# ---- database round trip -------------------------------------------------
tmp = tempfile.mkdtemp()
db = os.path.join(tmp, "t.db")
con = V.init_db(db)
con.execute("INSERT INTO valve_type (type_key,name,function,heater_v) VALUES (?,?,?,?)",
            ("EL84", "EL84", "output pentode", 6.3))
con.execute("INSERT INTO stock (type_key,box,qty,manufacturer) VALUES (?,?,?,?)",
            ("EL84", "3", 4, "Mullard"))
con.commit()

row = con.execute("SELECT * FROM v_stock WHERE type_key='EL84'").fetchone()
check("view joins type data", row["function"], "output pentode")
check("view carries quantity", row["qty"], 4)

# The per-lot detail fields are all optional, so a lot written without them
# reads back as NULL rather than failing.
check("position defaults to empty", row["position"], None)
check("origin defaults to empty", row["origin"], None)

con.execute("""UPDATE stock SET position=?, type1=?, origin=?, test_values=?, other=?
               WHERE type_key='EL84'""",
            ("B-12", "6BQ5", "ex Bush DAC90", "gm 9.8 mA/V", "boxed"))
con.commit()
row = con.execute("SELECT * FROM v_stock WHERE type_key='EL84'").fetchone()
check("view carries the lot position", row["position"], "B-12")
check("view carries the alt designation", row["type1"], "6BQ5")
check("view carries the origin", row["origin"], "ex Bush DAC90")
con.close()

# ---- migrating a database from before the per-lot fields existed ---------
# Built by hand as the pre-1.4 schema, then opened with init_db: the columns
# have to arrive without disturbing what was already in the table.
old_db = os.path.join(tmp, "old.db")
oc = sqlite3.connect(old_db)
oc.executescript("""
CREATE TABLE valve_type (type_key TEXT PRIMARY KEY, name TEXT NOT NULL, function TEXT,
    family TEXT, base TEXT, pins INTEGER, heater_v REAL, heater_a REAL, va_max REAL,
    pa_max REAL, gm REAL, mu REAL, power_out REAL, freq_max REAL, typical_use TEXT,
    equivalents TEXT, datasheet_path TEXT, datasheet_url TEXT, confidence TEXT, notes TEXT);
CREATE TABLE stock (id INTEGER PRIMARY KEY AUTOINCREMENT, type_key TEXT, box TEXT NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1, manufacturer TEXT, condition TEXT, date_added TEXT,
    notes TEXT);
CREATE VIEW v_stock AS SELECT s.id, s.box, s.qty, s.type_key, s.notes FROM stock s;
INSERT INTO valve_type (type_key,name,function) VALUES ('KT66','KT66','beam tetrode');
INSERT INTO stock (type_key,box,qty,manufacturer,notes) VALUES ('KT66','8',4,'GEC','matched');
""")
oc.commit()
oc.close()

con = V.init_db(old_db)
cols = {r[1] for r in con.execute("PRAGMA table_info(stock)")}
for col in ("position", "type1", "type2", "origin", "test_values", "other"):
    check_true(f"migration adds stock.{col}", col in cols)
row = con.execute("SELECT * FROM v_stock WHERE type_key='KT66'").fetchone()
check("migration keeps the quantity", row["qty"], 4)
check("migration keeps the maker", row["manufacturer"], "GEC")
check("migration keeps the notes", row["notes"], "matched")
check("migration rebuilds the stale view", row["position"], None)
check_true("migration is a no-op second time round", V.migrate(con) == [])
con.close()

# ---- CLI still runs ------------------------------------------------------
here = os.path.dirname(os.path.abspath(__file__))
for args in (["stats"], ["find", "EL84"], ["box", "3"],
             ["search", "--function", "pentode"], ["gaps"],
             ["search", "--position", "B-12"], ["search", "--alt", "6BQ5"],
             ["search", "--origin", "bush"], ["search", "--text", "bush"]):
    r = subprocess.run([sys.executable, os.path.join(here, "valves.py"), "--db", db] + args,
                       capture_output=True, text=True)
    check(f"cli {' '.join(args)} exits cleanly", r.returncode, 0)

# add/edit round trip: the lot id 'add' reports is the one 'edit' takes.
r = subprocess.run([sys.executable, os.path.join(here, "valves.py"), "--db", db,
                    "add", "GZ34", "--box", "30", "--qty", "3", "--position", "A-01",
                    "--type1", "5AR4", "--origin", "ex Leak Stereo 20"],
                   capture_output=True, text=True)
check("cli add with lot fields exits cleanly", r.returncode, 0)
con = V.connect(db)
lot = con.execute("SELECT * FROM stock WHERE type_key='GZ34'").fetchone()
check("add stores the position", lot["position"], "A-01")
check("add stores the alt designation", lot["type1"], "5AR4")
check_true("add reports the lot id", f"lot {lot['id']}" in r.stdout)
con.close()

r = subprocess.run([sys.executable, os.path.join(here, "valves.py"), "--db", db,
                    "edit", str(lot["id"]), "--position", "C-04", "--other", "unboxed"],
                   capture_output=True, text=True)
check("cli edit exits cleanly", r.returncode, 0)
con = V.connect(db)
lot = con.execute("SELECT * FROM stock WHERE type_key='GZ34'").fetchone()
check("edit updates what it was given", lot["position"], "C-04")
check("edit leaves the rest alone", lot["type1"], "5AR4")
con.close()

r = subprocess.run([sys.executable, os.path.join(here, "valves.py"), "--db", db,
                    "edit", "999999"], capture_output=True, text=True)
check("edit on a missing lot exits cleanly", r.returncode, 0)
check_true("edit on a missing lot says so", "no lot with id" in r.stdout)

# ---- snapshot / restore --------------------------------------------------
if os.path.exists(os.path.join(here, "data", "valves.sql")):
    out = os.path.join(tmp, "restored.db")
    r = subprocess.run([sys.executable, os.path.join(here, "snapshot.py"),
                        "--restore", "--force", "--db", out],
                       capture_output=True, text=True, cwd=here)
    check("restore exits cleanly", r.returncode, 0)
    if r.returncode == 0:
        c2 = sqlite3.connect(out)
        n = c2.execute("SELECT SUM(qty) FROM stock").fetchone()[0]
        check_true("restored database has stock", n and n > 0)
        c2.close()

# ---- report --------------------------------------------------------------
if failures:
    print(f"FAILED ({len(failures)})")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("all checks passed")
