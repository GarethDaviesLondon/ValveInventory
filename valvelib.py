"""
valvelib.py - shared core for the valve inventory system.

Holds the database schema, type-name normalisation, and the naming-convention
classifier that pre-fills function / heater voltage from the type designation.
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
CREATE TABLE IF NOT EXISTS stock (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type_key     TEXT REFERENCES valve_type(type_key) ON UPDATE CASCADE,
    box          TEXT NOT NULL,
    qty          INTEGER NOT NULL DEFAULT 1,
    manufacturer TEXT,
    condition    TEXT,                -- NOS, used, untested, matched pair, ...
    date_added   TEXT,
    notes        TEXT
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

CREATE INDEX IF NOT EXISTS idx_stock_type ON stock(type_key);
CREATE INDEX IF NOT EXISTS idx_stock_box  ON stock(box);
CREATE INDEX IF NOT EXISTS idx_socket_base ON socket(base);
CREATE INDEX IF NOT EXISTS idx_socket_box  ON socket(box);

-- Convenience view: stock joined to its type reference data.
CREATE VIEW IF NOT EXISTS v_stock AS
SELECT s.id, s.box, s.qty, COALESCE(t.name, s.type_key) AS type,
       s.type_key, s.manufacturer, s.condition,
       t.function, t.heater_v, t.pa_max, t.freq_max, t.base,
       t.datasheet_path, s.notes
FROM stock s LEFT JOIN valve_type t ON s.type_key = t.type_key;
"""


def connect(path=DB_DEFAULT):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(path=DB_DEFAULT):
    con = connect(path)
    con.executescript(SCHEMA)
    con.commit()
    return con


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

# Mullard/Philips (European) first letter -> heater rating
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

    # --- Transmitting types: 4CX250B, 3-500Z, QQV06-40, 4-125A ---
    if re.match(r"^\d+CX\d+", s) or re.match(r"^\d+\d{3}[ZA]$", s):
        out["family"] = "transmitting"
        out["function"] = "power tetrode" if "CX" in s else "power triode"
        return out
    if s.startswith("QQV"):
        out["family"] = "transmitting"
        out["function"] = "double beam tetrode"
        return out

    return out


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
