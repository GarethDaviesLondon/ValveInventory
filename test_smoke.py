#!/usr/bin/env python3
"""
test_smoke.py - fast checks that the pieces still fit together.

Run with:  python3 test_smoke.py
No test framework needed; exits non-zero on the first failure.
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
    if got != want:
        failures.append(f"{label}: got {got!r}, wanted {want!r}")


def check_true(label, cond):
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
con.close()

# ---- CLI still runs ------------------------------------------------------
here = os.path.dirname(os.path.abspath(__file__))
for args in (["stats"], ["find", "EL84"], ["box", "3"],
             ["search", "--function", "pentode"], ["gaps"]):
    r = subprocess.run([sys.executable, os.path.join(here, "valves.py"), "--db", db] + args,
                       capture_output=True, text=True)
    check(f"cli {' '.join(args)} exits cleanly", r.returncode, 0)

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
