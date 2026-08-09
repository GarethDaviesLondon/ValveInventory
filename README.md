# Valve inventory

A SQLite database and command-line tool for the attic collection.
**1,441 valves · 258 types · 36 boxes**, converted from the 38-tab spreadsheet.

## Files

| File | What it is |
|---|---|
| `valves.db` | The database. This is the only file that matters — back it up. |
| `valves.py` | The command-line tool. |
| `valves_gui.py` | The desktop window. Same database, different way in. |
| `valvelib.py` | Schema, type-name normalisation, and the code classifier. |
| `build_db.py` | One-off converter from the original workbook. Already run. |
| `fetch_datasheets.py` | Builds the local datasheet archive. |
| `snapshot.py` | Writes the diffable text snapshot in `data/` for version control. |
| `test_smoke.py` | Quick self-check that the pieces still fit together. |
| `data/` | Committed text snapshot of the collection. |
| `valve_inventory.xlsx` | Spreadsheet snapshot, regenerate any time with `export`. |

Requires Python 3.8+. `openpyxl` is only needed for export; `tkinter` only for the
GUI — on most systems it ships with Python, but Debian and Ubuntu split it out
into `python3-tk`.

## The window

```bash
python3 valves_gui.py
```

Both front ends read and write the same `valves.db`, so use whichever suits the
moment — the GUI for browsing and filling in datasheet figures, the CLI for
quick lookups and scripting.

- **Boxes down the left** — click one to filter, "All boxes" to clear.
- **Search row** — text, function, maker, and the numeric fields, which take
  the same `>20` / `<7` / `>=250` comparisons as the CLI.
- **Results table** — click any heading to sort. **Amber rows are types whose
  parameters are still inferred rather than read from a datasheet.**
- **Panel on the right** — the type's reference record, editable in place.
  *Save* keeps it as inferred; *Save + confirm* marks it confirmed and the row
  turns black. That amber-to-black transition is the progress bar for working
  through the collection.
- **Add stock / Take / Move / Delete lot** act on the selected row. *Add stock*
  creates the type automatically if it's new, classifying it as it goes.
- **Tools menu** — collection summary, what still needs data, duplicate
  candidates, and scanning the datasheet archive.

Merging duplicate types is command-line only, deliberately: it rewrites stock
rows and is not something to do by mis-click.

## Structure

Two tables, as discussed:

- **`valve_type`** — one row per type. Function, base, heater V/A, Va, Pa, gm, μ,
  power out, frequency, equivalents, and the path to its datasheet in the local archive.
- **`stock`** — one row per lot. Type, box, quantity, manufacturer, condition, notes.

Plus `sundry` for the sockets, screening cans and crystals, and `box` for
per-box location notes.

## Version control

The database is binary, so `valves.db` is gitignored and a text snapshot is
committed instead. Refresh it before you commit:

```bash
python3 snapshot.py          # writes data/types.csv, stock.csv, sundry.csv, valves.sql
git add -A && git commit -m "restocked box 12"
```

After cloning on another machine:

```bash
python3 snapshot.py --restore    # rebuilds valves.db from data/valves.sql
python3 test_smoke.py            # confirms everything fits together
```

The CSVs are what git will show you diffs in — you get a readable history of
what changed in the collection, which a committed `.db` would not give you.
`valves.sql` is the full dump that `--restore` rebuilds from.

### Before making the repository public

The `typical_use` and `notes` fields hold descriptive text carried over from the
original spreadsheet, much of it gathered from r-type.org. That text isn't yours
to republish. Either keep the repository private, or run:

```bash
python3 snapshot.py --strip-notes
```

which writes the exports without those fields. The classifications, parameters
and box locations — the actually useful part — are unaffected. Datasheet PDFs
are gitignored for the same reason; anyone cloning rebuilds their own archive
with `fetch_datasheets.py`.

## Command line

```bash
python3 valves.py box 12                  # what's in box 12
python3 valves.py find KT66               # which boxes hold KT66
python3 valves.py show ECC83              # full reference record
python3 valves.py stats                   # collection summary

# parametric search - this is the part the spreadsheet couldn't do
python3 valves.py search --function "output pentode" --heater 6.3
python3 valves.py search --pa '>20'                 # anode dissipation over 20W
python3 valves.py search --function triode --freq '>100'
python3 valves.py search --text nuvistor
python3 valves.py search --maker Mullard --box 5
```

Comparison operators work on `--heater --pa --va --freq --gm --mu`:
`'>20'`, `'<7'`, `'>=250'`, or a bare number for exact match. Quote them so the
shell doesn't read `>` as a redirect.

## Keeping it current

```bash
python3 valves.py add EL84 --box 25 --qty 6 --maker Mullard --condition NOS
python3 valves.py take EL84 --qty 2                  # used two in a build
python3 valves.py move GZ34 --frm 8 --to 12
python3 valves.py export                             # refresh the xlsx
```

`add` creates the type automatically if it's new, classifying it from its
designation as it goes.

## Filling in the reference data

Every parameter currently in `valve_type` was **inferred from the type
designation**, not read from a datasheet. Types are marked `inferred` until you
confirm them:

```bash
python3 valves.py set EL34 --pa 25 --va 800 --gm 11 --mu 11 \
                           --base octal --pins 8 --power-out 25 --confirm
```

`--confirm` flips the record to `confirmed`. `python3 valves.py gaps` lists what
still needs attention, ordered by how many you actually hold — so the effort goes
where it's worth spending.

Coverage from the classifier: **232 of 258** types have a function,
**197 of 258** have a heater rating. The rest are one-offs and service-coded
types the naming conventions don't cover.

## The datasheet archive

Three stages, and stages 1–2 want to run overnight:

```bash
python3 fetch_datasheets.py --index      # map the site (slow, resumable)
python3 fetch_datasheets.py --download   # pull only types you hold
python3 valves.py scan                   # link the files into the database
```

Then `python3 valves.py sheet EL34 --open` opens the PDF.

It fetches **only your 258 types and their equivalents**, not the whole site —
smaller download, and much kinder to a server that runs on donations. The default
2-second delay between requests is deliberate; please don't lower it. Both stages
resume if interrupted, so Ctrl-C is safe.

I couldn't verify Frank's exact directory layout when writing this (no network
access to that host from where it was built), so the crawler discovers the
structure rather than assuming it. If stage 1 comes back with very few hits, the
site layout has changed — the mirrors listed on its index page are the fallback.

For parameters rather than PDFs, `https://tdsl.duncanamps.com/show.php?des=EL34`
gives tabulated figures for filling in `set`, and there's a downloadable offline
edition.

## Housekeeping

```bash
python3 valves.py dupes                  # candidate duplicate type entries
python3 valves.py merge ECC83S ECC83     # dry run
python3 valves.py merge ECC83S ECC83 --yes
```

`dupes` is a *candidate* list matched on name similarity — it will offer
`30FL1`/`30FL14` and `PCF80`/`PCF801`, which are genuinely different valves.
Only merge what you know to be the same thing. Merging keeps all the stock and
records the old designation as an equivalent.

## Two entries need your eye

Carried over from the original sheets and flagged rather than guessed:

- **Box 14** — `?(Similar)`, unmarked, listed next to a Mullard TY4-125.
- **Box 17** — `207`, marked UNIDENTIFIED.

Also worth a decision: Box 17 holds `210`, `210HL` and `210 SS`, where the `210`
is noted as unmarked and *suspected* to be a 210. They're currently three
separate types.

## Conversion notes

Things the converter had to decide, so you can check them:

- **Box 6 ECL80** — recorded as 75, per your instruction (was "50+").
- **Box 8** — was one row per physical valve. Consolidated to 6 GEC KT66
  (one flagged `Loose Base`), 3 GZ34, 6 EF86, 1 R71.
- **Box 30** — this sheet had quantity in column C and the equivalent in
  column B, unlike every other sheet. Mapped accordingly.
- **Manufacturer vs equivalent** — several sheets used one column for both.
  Cells matching a known maker (Mullard, Mazda, GEC, Svetlana…) became
  manufacturer; everything else became an equivalent.
- **Continuation rows** — where a description spilled over several rows with a
  blank type cell (Box 23, 24, 26), the text was appended to the type's notes.
- **Heater codes** — `30` in a Mazda designation is read as 300 mA series-chain
  current, not volts, so those types have `heater_a` rather than `heater_v`.
