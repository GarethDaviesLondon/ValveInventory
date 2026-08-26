"""
valvelib.py - shared core for the valve inventory system.

Imported by both valves.py (CLI) and valves_gui.py (GUI); nothing in this
module is specific to either front end. It holds:

- SCHEMA: the SQLite schema (tables for valve types, stock, sundries,
  sockets and boxes), applied via executescript(), plus V_STOCK_SQL for the
  convenience view over stock and ADDED_COLUMNS listing the columns added
  to a table after its first release.
- connect() / init_db() / migrate(): open a database connection, ensure the
  schema exists, and bring an older database up to the current one in place.
- expand_lot() / take_from_lot() / check_lots() / lot_valves() /
  record_test(): the operations over individually-tracked valves and their
  test history, shared so both front ends treat a lot the same way.
- norm(): normalise a free-text type designation into a canonical lookup
  key (valve_type.type_key).
- classify(): given a normalised designation, guess the function, heater
  rating and family by trying several national naming conventions in turn
  (Mullard/Philips, British Mazda/Brimar, British GEC/Osram, American
  RETMA, Russian), falling back to the curated KNOWN table for designations
  that don't follow any of those schemes. Results are best-effort inferences
  meant to be confirmed against an actual datasheet, not authoritative data.
"""

import re
import sqlite3
import os

DB_DEFAULT = os.environ.get("VALVE_DB", "valves.db")
ARCHIVE_DEFAULT = os.environ.get("VALVE_ARCHIVE", "datasheets")

# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

SCHEMA = """
PRAGMA foreign_keys = ON;

-- One row per valve TYPE. The reference library.
CREATE TABLE IF NOT EXISTS valve_type (
    type_key       TEXT PRIMARY KEY,   -- normalised: uppercase, alnum only
    name           TEXT NOT NULL,      -- display name, e.g. "ECC83"
    function       TEXT,               -- triode, double triode, pentode, ...
    family         TEXT,               -- mullard/philips, mazda, us-ria, russian, ...
    base           TEXT,               -- B9A, octal, B7G, ...
    pins           INTEGER,
    heater_v       REAL,
    heater_a       REAL,
    va_max         REAL,               -- max anode voltage, V
    pa_max         REAL,               -- max anode dissipation, W
    gm             REAL,               -- mutual conductance, mA/V
    mu             REAL,               -- amplification factor
    power_out      REAL,               -- typical/max useful output, W
    freq_max       REAL,               -- useful upper frequency, MHz
    typical_use    TEXT,
    equivalents    TEXT,               -- space-separated
    datasheet_path TEXT,               -- relative path into the local archive
    datasheet_url  TEXT,
    confidence     TEXT DEFAULT 'inferred',  -- inferred | confirmed
    notes          TEXT
);

-- One row per physical lot: this many of this type, in this box.
-- position/type1/type2/origin/test_values/other were added later (v1.4) and
-- are optional throughout: a lot that only ever fills in box/qty behaves
-- exactly as it did before they existed. See migrate() for how they reach
-- databases created by an earlier version.
CREATE TABLE IF NOT EXISTS stock (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type_key     TEXT REFERENCES valve_type(type_key) ON UPDATE CASCADE,
    box          TEXT NOT NULL,
    position     TEXT,                -- where in the box, e.g. "B-12" (row-column)
    qty          INTEGER NOT NULL DEFAULT 1,
    manufacturer TEXT,
    condition    TEXT,                -- NOS, used, untested, matched pair, ...
    type1        TEXT,                -- secondary designation as marked, e.g. a US number
    type2        TEXT,                -- a further secondary designation
    origin       TEXT,                -- purchase, previous owner, or the set it came out of
    test_values  TEXT,                -- what it measured on the tester
    other        TEXT,                -- anything else: boxed/unboxed, printing, ...
    date_added   TEXT,
    notes        TEXT
);

-- One row per individually-tracked physical valve, belonging to a stock lot.
--
-- Optional by design: a lot carries its own qty and works perfectly well with
-- no rows here at all, which is the right answer for a box of a hundred
-- identical indicators nobody will ever test one by one. Expanding a lot
-- creates one row per valve it holds (see expand_lot), from which point each
-- valve can carry its own shelf position, its own markings, and its own test
-- history. stock.qty stays the authoritative count either way; the operations
-- that change it keep these rows in step, and check_lots() reports any lot
-- where the two have drifted apart.
CREATE TABLE IF NOT EXISTS valve (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id     INTEGER NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    position     TEXT,               -- where this one sits, e.g. "B-12"
    serial       TEXT,               -- serial, date code or etch - how you tell it apart
    manufacturer TEXT,               -- overrides the lot's, for a mixed lot
    condition    TEXT,               -- overrides the lot's
    notes        TEXT,
    added        TEXT
);

-- One row per test of one valve - or of one SECTION of one valve, since a
-- double triode reads separately per section and matching it for phase-inverter
-- use is exactly what those two readings are for.
--
-- A test is an event, not a property: a valve tested in 2019 and again today
-- has two rows here, and the trend between them is the useful part. Every
-- reading is nullable because no single tester produces all of them - an
-- emission tester gives one figure, an AVO VCM163 reads anode current and
-- mutual conductance simultaneously plus separate gas and insulation tests,
-- a curve tracer gives everything.
--
-- Units follow British practice throughout, since that is what the collection
-- and its testers are: gm in mA/V, not the micromhos an American tester shows
-- (1 mA/V = 1000 umho).
CREATE TABLE IF NOT EXISTS valve_test (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    valve_id        INTEGER NOT NULL REFERENCES valve(id) ON DELETE CASCADE,
    tested_on       TEXT,            -- ISO date
    tester          TEXT,            -- "AVO VCM163", "uTracer 6", ...
    section         TEXT,            -- "a"/"b" on a multi-section valve, else NULL
    -- conditions the readings were taken under: a gm figure means nothing
    -- without them, and the same valve reads differently under fixed and
    -- auto bias
    va              REAL,            -- anode volts at test
    vg              REAL,            -- grid bias at test
    bias_mode       TEXT,            -- fixed | auto
    -- readings
    ia              REAL,            -- anode (plate) current, mA
    ig2             REAL,            -- screen current, mA
    gm              REAL,            -- mutual conductance, mA/V
    gm_pct          REAL,            -- gm as a percentage of the nominal figure
    emission_pct    REAL,            -- an emission tester's single reading, %
    -- fault tests
    gas_ua          REAL,            -- gas / grid current, uA
    insulation_mohm REAL,            -- interelectrode insulation, Mohm
    heater_cathode  TEXT,            -- heater-cathode leakage: a figure, or pass/fail
    shorts          TEXT,            -- interelectrode shorts: pass/fail
    verdict         TEXT,            -- good | weak | short | failed | ...
    notes           TEXT
);

-- Non-valve items: screening cans, crystals, chimneys - the general catch-all.
CREATE TABLE IF NOT EXISTS sundry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    box         TEXT NOT NULL,
    description TEXT NOT NULL,
    qty         INTEGER DEFAULT 1,
    notes       TEXT
);

-- One row per lot of valve bases / sockets - B9A, Octal, B7G, Loctal, UX4...
-- Split out from sundry so it's searchable by base type rather than buried
-- in free text.
CREATE TABLE IF NOT EXISTS socket (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    base      TEXT NOT NULL,
    box       TEXT NOT NULL,
    qty       INTEGER NOT NULL DEFAULT 1,
    condition TEXT,
    notes     TEXT
);

CREATE TABLE IF NOT EXISTS box (
    box      TEXT PRIMARY KEY,
    location TEXT,
    label    TEXT,
    notes    TEXT
);

-- Reference documents. Two uses of the same row shape, told apart by
-- whether type_key is set:
--   * type_key NOT NULL - an extra datasheet for that type, beyond the one
--     "primary" sheet valve_type.datasheet_path/datasheet_url already
--     covers (kept as-is so the existing one-click Open datasheet flow is
--     unchanged - this table is for the *additional* ones, e.g. a second
--     manufacturer's sheet, or an app note).
--   * type_key NULL - general reference material not tied to one type, e.g.
--     "Care and feeding of power tubes" - shown in the Docs tab instead.
CREATE TABLE IF NOT EXISTS document (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    type_key TEXT REFERENCES valve_type(type_key) ON UPDATE CASCADE,
    title    TEXT NOT NULL,
    abstract TEXT,               -- short description / what it covers
    path     TEXT,               -- relative path into the local archive, if a copy is held
    url      TEXT,               -- source URL, if any
    added    TEXT
);

CREATE INDEX IF NOT EXISTS idx_stock_type ON stock(type_key);
CREATE INDEX IF NOT EXISTS idx_stock_box  ON stock(box);
CREATE INDEX IF NOT EXISTS idx_socket_base ON socket(base);
CREATE INDEX IF NOT EXISTS idx_socket_box  ON socket(box);
CREATE INDEX IF NOT EXISTS idx_document_type ON document(type_key);
CREATE INDEX IF NOT EXISTS idx_valve_stock ON valve(stock_id);
CREATE INDEX IF NOT EXISTS idx_valve_test_valve ON valve_test(valve_id);
"""

# Convenience view: stock joined to its type reference data. Kept out of
# SCHEMA because CREATE VIEW IF NOT EXISTS would leave an older database
# sitting on an older view definition for ever; migrate() drops and recreates
# it instead, so the view always matches the columns stock actually has.
V_STOCK_SQL = """
CREATE VIEW v_stock AS
SELECT s.id, s.box, s.position, s.qty, COALESCE(t.name, s.type_key) AS type,
       s.type_key, s.type1, s.type2, s.manufacturer, s.condition,
       s.origin, s.test_values, s.other,
       (SELECT COUNT(*) FROM valve v WHERE v.stock_id = s.id) AS individuals,
       t.function, t.heater_v, t.pa_max, t.freq_max, t.base,
       t.datasheet_path, s.notes
FROM stock s LEFT JOIN valve_type t ON s.type_key = t.type_key;
"""

# Everything a test can record, as (column, label, unit, kind). One list so the
# CLI options, the GUI form, the spreadsheet export and the snapshot all describe
# the same test the same way. Grouped in reading order: when it was done and
# under what conditions, then what the meters said, then the fault tests.
# The third element is a real unit or blank - never a hint, so it can be
# appended to a value without checking. Anything a user needs telling about
# the accepted values goes in the label, where a form shows it.
TEST_FIELDS = [
    ("tested_on", "Tested on", "", str),
    ("tester", "Tester", "", str),
    ("section", "Section (a/b, blank if single)", "", str),
    ("va", "Va at test", "V", float),
    ("vg", "Vg at test", "V", float),
    ("bias_mode", "Bias mode (fixed/auto)", "", str),
    ("ia", "Anode current Ia", "mA", float),
    ("ig2", "Screen current Ig2", "mA", float),
    ("gm", "Mutual conductance gm", "mA/V", float),
    ("gm_pct", "gm as % of nominal", "%", float),
    ("emission_pct", "Emission", "%", float),
    ("gas_ua", "Gas / grid current", "uA", float),
    ("insulation_mohm", "Insulation", "Mohm", float),
    ("heater_cathode", "Heater-cathode (Mohm, or pass/fail)", "", str),
    ("shorts", "Shorts (pass/fail)", "", str),
    ("verdict", "Verdict (good/weak/short/failed)", "", str),
    ("notes", "Notes", "", str),
]

# Fields an individual valve carries in its own right, as (column, label).
# Everything else about it - type, box, origin - belongs to its lot.
VALVE_FIELDS = [
    ("position", "Position in box"),
    ("serial", "Serial / date code"),
    ("manufacturer", "Manufacturer"),
    ("condition", "Condition"),
    ("notes", "Notes"),
]

# Columns added to existing tables after their first release, applied by
# migrate() to databases that predate them: table -> [(column, declaration)].
ADDED_COLUMNS = {
    "stock": [
        ("position", "TEXT"),
        ("type1", "TEXT"),
        ("type2", "TEXT"),
        ("origin", "TEXT"),
        ("test_values", "TEXT"),
        ("other", "TEXT"),
    ],
}


def connect(path=DB_DEFAULT):
    """Open a SQLite connection to the inventory database.

    Sets row_factory to sqlite3.Row (so results can be accessed by column
    name) and enables foreign-key enforcement, which SQLite otherwise
    leaves off per-connection. Does not create or migrate the schema -
    use init_db() for that. Returns the open connection.
    """
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def migrate(con):
    """Bring an existing database up to the current schema, in place.

    Two jobs, both idempotent and both safe on a database that is already
    current (they simply find nothing to do):

    1. Add any column in ADDED_COLUMNS that the table doesn't have yet.
       SQLite's ALTER TABLE ADD COLUMN only appends a nullable column, so
       existing rows keep every value they had and read back NULL for the
       new one - no data is rewritten or moved.
    2. Rebuild the v_stock view, which has to name the stock columns
       explicitly and so goes stale the moment stock gains one.

    Returns the list of "table.column" strings actually added, so a caller
    can report what it did; the empty list means the database was already
    up to date.
    """
    added = []
    for table, columns in ADDED_COLUMNS.items():
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                           (table,)).fetchone():
            continue      # table itself is new - SCHEMA has just created it in full
        have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        for name, decl in columns:
            if name not in have:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
                added.append(f"{table}.{name}")
    con.execute("DROP VIEW IF EXISTS v_stock")
    con.executescript(V_STOCK_SQL)
    con.commit()
    return added


def init_db(path=DB_DEFAULT):
    """Open a connection and ensure the schema is present and current.

    Runs SCHEMA via executescript() - every statement in it is idempotent
    (CREATE TABLE/INDEX IF NOT EXISTS) - then migrate() to add any column a
    database from an older version is missing and rebuild the v_stock view.
    Safe to call on a brand-new file (first-run setup), on a current
    database (a no-op), or on an older one (an in-place upgrade that leaves
    existing data untouched). Returns the open connection.
    """
    con = connect(path)
    con.executescript(SCHEMA)
    migrate(con)
    return con


# --------------------------------------------------------------------------
# Lots and the individual valves in them
# --------------------------------------------------------------------------

def expand_lot(con, stock_id, upto=None):
    """Create individual valve rows for a lot until it has one per valve held.

    Idempotent and additive: it only ever tops a lot up to `upto` (default the
    lot's own qty), so running it twice creates nothing the second time, and a
    lot that already has some individuals tracked keeps them and their test
    history. Returns the number of rows created.

    Nothing else in the tool requires a lot to be expanded - this is the step
    that opts one lot in to per-valve tracking.
    """
    lot = con.execute("SELECT id, qty FROM stock WHERE id=?", (stock_id,)).fetchone()
    if not lot:
        return 0
    want = lot["qty"] if upto is None else upto
    have = con.execute("SELECT COUNT(*) c FROM valve WHERE stock_id=?", (stock_id,)).fetchone()["c"]
    today = _today()
    for _ in range(max(0, want - have)):
        con.execute("INSERT INTO valve (stock_id, added) VALUES (?,?)", (stock_id, today))
    con.commit()
    return max(0, want - have)


def take_from_lot(con, stock_id, n):
    """Remove `n` valves from a lot, keeping its individual rows in step.

    Reduces qty (deleting the lot outright when nothing is left) and, if the
    lot has individual rows, deletes that many of them. Which ones: the least
    documented first - untested before tested, unmarked before serial-numbered,
    unplaced before placed - so using valves up never quietly destroys test
    history you took the trouble to record. Deleting a valve row takes its
    tests with it (ON DELETE CASCADE).

    Returns the number actually taken, which is less than `n` if the lot
    didn't hold that many.
    """
    lot = con.execute("SELECT id, qty FROM stock WHERE id=?", (stock_id,)).fetchone()
    if not lot:
        return 0
    took = min(n, lot["qty"])
    if took <= 0:
        return 0
    doomed = [r["id"] for r in con.execute("""
        SELECT v.id FROM valve v WHERE v.stock_id = ?
        ORDER BY (SELECT COUNT(*) FROM valve_test t WHERE t.valve_id = v.id),
                 v.serial IS NOT NULL, v.position IS NOT NULL, v.id DESC
        LIMIT ?""", (stock_id, took))]
    for vid in doomed:
        con.execute("DELETE FROM valve WHERE id=?", (vid,))
    if took >= lot["qty"]:
        con.execute("DELETE FROM stock WHERE id=?", (stock_id,))
    else:
        con.execute("UPDATE stock SET qty = qty - ? WHERE id=?", (took, stock_id))
    con.commit()
    return took


def check_lots(con):
    """Report lots whose individual valve rows have drifted out of step with qty.

    A lot is consistent when it has either no individual rows at all (not
    expanded - the normal state) or exactly qty of them. Anything else means
    an edit went in that this module didn't mediate, so it's reported rather
    than silently corrected: which side is right is a judgement about the
    actual shelf, not one to make in code.

    Returns a list of dicts with the lot id, type, box, qty and individual
    count - empty when everything is in step.
    """
    return [dict(r) for r in con.execute("""
        SELECT s.id, s.box, s.qty, COALESCE(t.name, s.type_key) AS type,
               (SELECT COUNT(*) FROM valve v WHERE v.stock_id = s.id) AS individuals
        FROM stock s LEFT JOIN valve_type t ON s.type_key = t.type_key
        WHERE individuals NOT IN (0, s.qty)
        ORDER BY CAST(s.box AS INTEGER), s.box""")]


def lot_valves(con, stock_id):
    """Return a lot's individual valves, each with a summary of its latest test.

    The summary columns (last_tested, last_gm, last_ia, last_verdict, tests)
    come from that valve's most recent valve_test row, so a listing can show
    the current state of each valve without a second query per row. A valve
    that has never been tested still appears, with those columns NULL and
    tests = 0.
    """
    return [dict(r) for r in con.execute("""
        SELECT v.*,
               (SELECT COUNT(*) FROM valve_test t WHERE t.valve_id = v.id) AS tests,
               lt.tested_on AS last_tested, lt.gm AS last_gm, lt.ia AS last_ia,
               lt.gm_pct AS last_gm_pct, lt.verdict AS last_verdict
        FROM valve v
        LEFT JOIN valve_test lt ON lt.id = (
            SELECT t.id FROM valve_test t WHERE t.valve_id = v.id
            ORDER BY t.tested_on DESC, t.id DESC LIMIT 1)
        WHERE v.stock_id = ?
        ORDER BY v.position IS NULL, v.position, v.id""", (stock_id,))]


def record_test(con, valve_id, values):
    """Insert one valve_test row from a {column: value} dict, ignoring blanks.

    Only keys named in TEST_FIELDS are written, so a caller can hand over a
    whole form's worth of values without filtering first. tested_on defaults
    to today when not given. Returns the new row's id.
    """
    cols = [c for c, _l, _u, _k in TEST_FIELDS
            if values.get(c) is not None and values.get(c) != ""]
    data = [values[c] for c in cols]
    if "tested_on" not in cols:
        cols.append("tested_on")
        data.append(_today())
    cols.append("valve_id")
    data.append(valve_id)
    cur = con.execute(
        f"INSERT INTO valve_test ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", data)
    con.commit()
    return cur.lastrowid


def _today():
    """Today as an ISO date string. Local import so valvelib stays cheap to
    import for the classifier-only callers that never touch a database."""
    import datetime
    return datetime.date.today().isoformat()


# --------------------------------------------------------------------------
# Type-name normalisation
# --------------------------------------------------------------------------

def norm(name):
    """Normalise a type designation to a lookup key.

    Uppercase, strip service prefixes and all non-alphanumerics.
    'jan 7289' -> '7289'   'PY 4-400' -> 'PY4400'   'ecc83s' -> 'ECC83S'
    """
    if name is None:
        return None
    s = str(name).strip().upper()
    s = re.sub(r"^(JAN|JAN-|CV-)\s*", "", s)
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s or None


# --------------------------------------------------------------------------
# Naming-convention classifier
# --------------------------------------------------------------------------

# Mullard/Philips (European) first letter -> heater rating.
# Each value is (heater_v, heater_a): valve types are heated either at a
# fixed voltage (series of directly-heated/parallel types, e.g. "E" = 6.3V)
# or a fixed current (series-string heaters wired chain-fashion, e.g. "P" =
# 300mA) - exactly one of the pair is populated, the other is None.
_EU_HEATER = {
    "A": (4.0, None), "B": (None, 0.18), "C": (None, 0.20),
    "D": (1.4, None), "E": (6.3, None), "F": (13.0, None),
    "G": (5.0, None), "H": (None, 0.15), "K": (2.0, None),
    "L": (None, 0.45), "P": (None, 0.30), "U": (None, 0.10),
    "V": (None, 0.05), "X": (None, 0.60), "Y": (None, 0.45),
}

# Mullard/Philips subsequent letters -> section function
_EU_SECTION = {
    "A": "signal diode", "B": "double diode", "C": "triode",
    "D": "power triode", "E": "tetrode", "F": "pentode",
    "H": "hexode/heptode", "K": "octode", "L": "output pentode/tetrode",
    "M": "tuning indicator", "N": "thyratron", "Q": "enneode",
    "X": "gas full-wave rectifier", "Y": "HV half-wave rectifier",
    "Z": "full-wave rectifier",
}

# British Mazda / Brimar style: leading number is heater, letters are function
_UK_SECTION = {
    "C": "triode-pentode (frequency changer)", "D": "diode",
    "F": "RF pentode", "L": "double triode / output",
    "P": "output pentode/tetrode", "PL": "output pentode",
    "FL": "triode-tetrode", "U": "rectifier",
}

# Russian (Cyrillic transliterated) class letters
_RU_SECTION = {
    "N": "double triode", "P": "output pentode/beam tetrode",
    "ZH": "RF pentode", "S": "triode", "TS": "rectifier",
    "H": "double triode", "K": "variable-mu pentode",
    "E": "tuning indicator", "D": "diode", "J": "RF pentode",
    "C": "triode",
}


# British GEC / Osram / Marconi codes: letter prefix then digits only.
# Checked after the European code because several prefixes collide.
# Each value is (function, heater_v); heater_v is usually None because the
# GEC/Osram scheme doesn't encode heater rating in the type code itself.
_GB_PREFIX = {
    "KT": ("beam tetrode (output)", 6.3),
    "DH": ("double diode triode", None),
    "DD": ("double diode", None),
    "QP": ("double pentode (QPP output)", None),
    "HL": ("triode (general purpose)", None),
    "MH": ("triode", None),
    "MS": ("variable-mu tetrode", None),
    "N":  ("output pentode", None),
    "U":  ("rectifier", None),
    "W":  ("variable-mu RF pentode", None),
    "X":  ("frequency changer (heptode/octode)", None),
    "Z":  ("RF pentode", None),
    "D":  ("diode", None),
    "L":  ("triode", None),
    "S":  ("screen-grid tetrode", None),
}

# Leading numbers that really are heater ratings in the British Mazda scheme
_UK_HEATER_NUMS = {4, 6, 10, 20, 25, 30, 35}
# Leading numbers that really are heater volts in the American scheme
_US_HEATER_NUMS = {5: 5.0, 6: 6.3, 7: 7.0, 12: 12.6, 25: 25.0, 26: 26.5,
                   35: 35.0, 50: 50.0, 117: 117.0}


# Types whose designation carries no usable function code. Curated by hand
# for the types actually held; extend as the collection grows.
# Each value is (function, heater_v); heater_v is None where not known/fixed.
KNOWN = {
    "6AU6":    ("RF pentode", 6.3), "6BA6": ("variable-mu RF pentode", 6.3),
    "6BW6":    ("beam tetrode (output)", 6.3), "6BW7": ("RF pentode", 6.3),
    "6SN7":    ("double triode", 6.3), "6SK7": ("variable-mu RF pentode", 6.3),
    "6J5":     ("triode", 6.3), "6K7": ("variable-mu RF pentode", 6.3),
    "6V6":     ("beam tetrode (output)", 6.3), "6X4": ("full-wave rectifier", 6.3),
    "6AG7":    ("output pentode", 6.3), "6AS6": ("RF pentode", 6.3),
    "6AJ7":    ("RF pentode", 6.3), "6J6A": ("double triode (VHF)", 6.3),
    "6CZ5":    ("beam pentode (output)", 6.3), "6AU5GT": ("beam pentode (line output)", 6.3),
    "6GH8A":   ("triode + pentode", 6.3), "6ES8": ("double triode (VHF)", 6.3),
    "6146":    ("beam tetrode (transmitting)", 6.3),
    "6146B":   ("beam tetrode (transmitting)", 6.3),
    "6146W":   ("beam tetrode (transmitting)", 6.3),
    "12BY7":   ("video/driver pentode", 12.6), "12BA6": ("variable-mu RF pentode", 12.6),
    "5U4G":    ("full-wave rectifier", 5.0), "5Y3": ("full-wave rectifier", 5.0),
    "807":     ("beam tetrode (transmitting)", 6.3),
    "813":     ("beam tetrode (transmitting)", 10.0),
    "811":     ("power triode (transmitting)", 6.3),
    "8136":    ("beam tetrode", 6.3), "8D3": ("RF pentode", 6.3),
    "7A7":     ("variable-mu RF pentode", 7.0),
    "OA2":     ("voltage stabiliser (cold cathode)", None),
    "OB2":     ("voltage stabiliser (cold cathode)", None),
    "VR150":   ("voltage stabiliser (cold cathode)", None),
    "150B2":   ("voltage stabiliser (cold cathode)", None),
    "150C4":   ("voltage stabiliser (cold cathode)", None),
    "75C1":    ("voltage stabiliser (cold cathode)", None),
    "QS15015": ("voltage stabiliser (cold cathode)", None),
    "2P29":    ("RF/audio pentode", 2.2), "6E6PG": ("high-gain tetrode", 6.3),
    "6J9P":    ("RF pentode", 6.3), "6J1P": ("RF pentode", 6.3),
    "6N2P":    ("double triode", 6.3), "6H2N": ("double triode", 6.3),
    "6C19N":   ("triode (series regulator)", 6.3),
    "3500Z":   ("power triode (transmitting)", 5.0),
    "31000Z":  ("power triode (transmitting)", 7.5),
    "4125A":   ("power tetrode (transmitting)", 5.0),
    "465A":    ("power tetrode (transmitting)", 6.0),
    "EV3A":    ("nixie / 7-segment indicator", None),
    "726A":    ("reflex klystron", 6.3),
    # Mazda / Osram battery and service types
    "OV65":    ("output pentode (battery)", 2.0),
    "CV4014":  ("RF pentode (special quality)", 6.3),
    "CV1375":  ("variable-mu RF pentode", 6.3),
    "CV2799":  ("double beam tetrode (transmitting)", 6.3),
    "CV2466":  ("double beam tetrode (transmitting)", 6.3),
    "CV124":   ("beam tetrode (transmitting)", 6.3),
    "CV5215":  ("triode + pentode", 6.3),
    "CV287":   ("voltage stabiliser (cold cathode)", None),
    "CV1833":  ("voltage stabiliser (cold cathode)", None),
    "CV320":   ("cathode ray tube", None),
    "CV4060":  ("RF pentode (special quality)", 6.3),
    # Russian types whose codes collide with British ones
    "6C17":    ("UHF triode", 6.3), "6C19N": ("triode (series regulator)", 6.3),
    "6H1NE8":  ("double triode", 6.3), "6N1N": ("beam tetrode (output)", 6.3),
    "2XX27N":  ("RF pentode", 2.2), "CF15N2": ("voltage stabiliser (cold cathode)", None),
    "GS14":    ("UHF power triode", 6.3), "GS15B": ("power tetrode", None),
    "GS23":    ("power triode", None), "GS35": ("power triode", None),
    "GU35":    ("power tetrode", 6.3), "GU46": ("power tetrode", None),
    "GI7B":    ("UHF power triode", None), "GI15B": ("UHF power triode", None),
    "6C51HB":  ("nuvistor triode", 6.3),
    # transmitting / misc
    "JAN7289": ("UHF ceramic triode", 6.3), "7289": ("UHF ceramic triode", 6.3),
    "2C39A":   ("UHF ceramic triode", 6.3), "2C34": ("double triode (VHF)", 6.3),
    "5B251":   ("beam tetrode (transmitting)", 6.3),
    "ACT22":   ("power triode (UHF)", None),
    "VT61A":   ("double triode (VHF)", None),
    "QY3125":  ("power tetrode (transmitting)", None),
    "PY4400":  ("power tetrode (transmitting)", None),
    "TY4125":  ("power tetrode (transmitting)", None),
    "3CX1200A7": ("power triode (transmitting)", None),
    "4CX250B": ("power tetrode (transmitting)", 6.0),
    "4CX350":  ("power tetrode (transmitting)", 6.0),
    "E3062":   ("power triode (industrial)", None),
    "R71":     ("rectifier", None),
    "ELC6J":   ("thyratron (xenon)", 2.5),
}


def classify(name):
    """Infer function / heater / family from a type designation.

    Returns a dict of inferred fields. Everything here is a guess from the
    naming convention and should be overwritten once a datasheet is read;
    where a code is ambiguous the field is left blank rather than guessed.
    """
    out = {}
    s = norm(name)
    if not s:
        return out

    # --- curated table wins over any code rule ---
    if s in KNOWN:
        fn, hv = KNOWN[s]
        out["function"] = fn
        if hv is not None:
            out["heater_v"] = hv
        return out

    # --- GEC beam tetrodes: KT66, KT61, KT88. Collides with the European
    #     code (K = 2V battery heater) so it is resolved first. ---
    m = re.match(r"^KT(\d{2,3})$", s)
    if m:
        return {"family": "british (GEC)", "function": "beam tetrode (output)",
                "heater_v": 6.3}

    # --- European Mullard/Philips: letters then digits, e.g. ECC83, PCL85 ---
    m = re.match(r"^([A-Z]{2,4})(\d{2,3})[A-Z]*$", s)
    if m:
        letters, _digits = m.groups()
        h = _EU_HEATER.get(letters[0])
        if h:
            out["family"] = "european (Mullard/Philips code)"
            if h[0] is not None:
                out["heater_v"] = h[0]
            if h[1] is not None:
                out["heater_a"] = h[1]
            secs = [_EU_SECTION[c] for c in letters[1:] if c in _EU_SECTION]
            if secs:
                if len(secs) > 1 and len(set(secs)) == 1:
                    out["function"] = "double " + secs[0]
                else:
                    out["function"] = " + ".join(secs)
            return out

    # --- British Mazda / Brimar: 30C15, 6F28, 30PL14, 10F1.
    #     Only accepted when BOTH the leading number and the letter group are
    #     valid in that scheme, otherwise 8D3 and 6AU6 get mis-read. ---
    m = re.match(r"^(\d{1,2})([A-Z]{1,2})(\d{1,3})$", s)
    if m:
        num, letters, _ = m.groups()
        n = int(num)
        if n in _UK_HEATER_NUMS and letters in _UK_SECTION:
            out["family"] = "british (Mazda/Brimar code)"
            if n >= 20:
                out["heater_a"] = n / 100.0      # 30 = 300 mA series chain
            else:
                out["heater_v"] = 6.3 if n == 6 else float(n)
            out["function"] = _UK_SECTION[letters]
            return out

    # --- Russian: 6N1P, 6S19P, 6J1P, 2P29 (trailing P/N is the giveaway) ---
    m = re.match(r"^(\d{1,2})([A-Z]{1,2})(\d{1,2})([PNKS])$", s)
    if m:
        num, letters, _, _ = m.groups()
        out["family"] = "russian"
        out["heater_v"] = 6.3 if num == "6" else float(num)
        fn = _RU_SECTION.get(letters)
        if fn:
            out["function"] = fn
        return out

    # --- American RIA/RETMA: 6AU6, 12AX7, 5U4G, 6SN7 ---
    m = re.match(r"^(\d{1,3})([A-Z]{1,3})(\d{1,2})([A-Z]*)$", s)
    if m:
        num, _letters, count, _suffix = m.groups()
        v = int(num)
        if v in _US_HEATER_NUMS:
            out["family"] = "american (RETMA code)"
            out["heater_v"] = _US_HEATER_NUMS[v]
            # The trailing digit is the electrode count, not the function
            # (6X4 is a rectifier, 6SN7 a double triode, both "count 4/7"),
            # so no function is inferred here - see KNOWN below.
            return out

    # --- British GEC/Osram: N37, U319, Z749, D77, W77, X79, DH77, QP22 ---
    m = re.match(r"^([A-Z]{1,2})(\d{2,3})[A-Z]?$", s)
    if m:
        letters, _ = m.groups()
        if letters in _GB_PREFIX:
            fn, hv = _GB_PREFIX[letters]
            out["family"] = "british (GEC/Osram code)"
            out["function"] = fn
            if hv:
                out["heater_v"] = hv
            return out

    # --- Transmitting types: 4CX250B, 3-500Z, QQV06-40, 4-125A. norm()
    #     strips the hyphen, so "3-500Z" arrives as "3500Z"; the second
    #     pattern (\d+\d{3}[ZA]) just requires 4+ digits ending in Z/A,
    #     which is enough to catch that "electrode count - anode
    #     dissipation - suffix" shape without a stricter split. ---
    if re.match(r"^\d+CX\d+", s) or re.match(r"^\d+\d{3}[ZA]$", s):
        out["family"] = "transmitting"
        out["function"] = "power tetrode" if "CX" in s else "power triode"
        return out
    if s.startswith("QQV"):
        out["family"] = "transmitting"
        out["function"] = "double beam tetrode"
        return out

    return out


# Coarse function categories for grouping/filtering in the GUI and reports.
# Each entry is (display label, [substrings to match, case-insensitively,
# against a valve_type.function value]). Order matters only in that the
# first matching label wins - kept broad-to-specific isn't required here
# since the keyword lists don't overlap. Not used by classify() itself;
# consumed by front ends (see valves_gui.function_group()) to collapse the
# many free-text function strings classify() can produce into a short list
# a user can filter by.
FUNCTION_GROUPS = [
    ("triode", ["triode"]),
    ("double triode", ["double triode", "twin triode", "dual triode"]),
    ("tetrode", ["tetrode"]),
    ("pentode", ["pentode"]),
    ("rectifier", ["rectifier", "efficiency diode", "eht"]),
    ("diode", ["diode"]),
    ("frequency changer", ["heptode", "hexode", "octode", "frequency changer"]),
    ("stabiliser", ["stabiliser", "stabilizer", "voltage reference"]),
    ("indicator", ["tuning indicator", "magic eye", "nixie"]),
    ("klystron", ["klystron"]),
]
