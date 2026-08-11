# Quick start

You've been given an exported copy of a valve inventory: the tools and a
snapshot of the database, zipped up. This gets you from "just unzipped it"
to a working database in a few minutes.

## 1. Requirements

- Python 3.8 or later (`python3 --version` to check).
- `tkinter` for the desktop window - ships with most Python installs; on
  Debian/Ubuntu you may need `sudo apt install python3-tk`.
- `openpyxl` only if you want to export to Excel: `pip install openpyxl`.

## 2. Unzip and rebuild the database

The database itself (`valves.db`) isn't included - it's binary and would
just bloat the zip. What's included is `data/`, a text snapshot that
rebuilds it:

```bash
cd valve-inventory          # wherever you unzipped it
python3 snapshot.py --restore
python3 test_smoke.py       # confirms everything fits together
```

## 3. Use it

```bash
python3 valves_gui.py       # the desktop window
python3 valves.py stats     # or drive it from the command line
```

See `README.md` for the full command reference, the GUI walkthrough, and
what each file is for.

## 4. Datasheets

The PDF archive itself isn't included (hundreds of MB of third-party
files). Rebuild your own copy any time:

```bash
python3 fetch_datasheets.py --index      # map the site (slow, resumable, run once)
python3 fetch_datasheets.py --download   # pull only the types in this database
python3 valves.py scan                   # link the files in
```

## 5. Adding your own valves

Two ways in:

- **The GUI or CLI directly** - `valves.py add TYPE --box N --qty N`, or the
  "Add stock" button. Good for a handful at a time.
- **Bulk upload** - if you're bringing in a whole spreadsheet or a big batch,
  use `upload_template.csv` (see the header row for the columns) and
  `valves.py import-csv <file>`. Every new type gets classified automatically
  from its designation the same way `add` does.

## 6. Filling in reference data

New types start with only what the naming convention can infer - a real
datasheet reading is what actually confirms them. `valves.py gaps` (or
**Tools > What needs data** in the GUI) lists what's missing, ordered by how
many you hold. If you have Claude Code or claude.ai available, the GUI's
**Tools > Generate research prompt...** writes out a ready-to-paste prompt
that asks Claude to research whatever's still unconfirmed and hand back
data in a format `import_researched.py` can apply directly - see that
menu item for the exact steps.
