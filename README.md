# Valve inventory

A SQLite database and command-line tool for the attic collection.
**1,441 valves · 253 types · 36 boxes**, converted from the 38-tab spreadsheet
(a handful of duplicate/dual-marked entries have since been merged).

## History

I built this to catalogue my own valve (vacuum tube) collection, previously
tracked across a 38-tab spreadsheet that had outgrown what a spreadsheet
could usefully do — particularly parametric search ("what output pentodes
over 20W do I have?"). The database that ships with this repository
(`data/`, restored into `valves.db`) **is my actual stock**: real box
locations in my attic, not sample data.

If you're here for your own collection rather than mine, that's exactly
what this tool is for too — see
[Starting your own collection](#starting-your-own-collection) below, and
the same walkthrough in the Installation Manual (`docs/INSTALLATION_MANUAL.pdf`).

## License, warranty, and risk

MIT-licensed — see [LICENSE](LICENSE). MIT is about as permissive as
licenses get; its one real obligation, keeping the copyright notice
attached, is also what gives it attribution. (The data in `data/` carries
its own, separate note in `LICENSE` — some of the descriptive text there is
third-party material gathered from reference sites, not mine to relicense.)

**This software is provided without warranty of any kind, express or
implied, and you use it entirely at your own risk.** It's hobbyist tooling
built for one person's attic, not a certified reference — treat every
`inferred` parameter as a lead to verify against a real datasheet, not a
settled fact, especially before relying on it for anything involving the
lethal voltages a valve amplifier runs at.

By downloading, installing, or running this application, you're confirming
that you've reviewed the source for yourself — it's a modest, readable
Python codebase, with no network access beyond what's documented
(`fetch_datasheets.py`, the optional Claude-research workflow, and PyPI for
the two optional dependencies) — and that you accept these terms.

## Community

This started as a fix for one person's attic, but the parametric search,
the naming-convention classifier, and the Claude-assisted research/datasheet
workflows are useful to anyone cataloguing valves. The hobbyist tube
community has always run on people writing down what they know for the next
person — a datasheet rescued from a defunct site, a base wiring diagram
redrawn from memory, a substitution someone actually tried. If this is
useful to you, bug reports, pull requests, and researched-parameter
contributions are all welcome; if you extend it for a different kind of
collection, I'd like to hear about it.

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
| `upload_template.csv` | Column layout for bulk-adding stock — `import-csv` / Tools > Import upload CSV. |
| `import_researched.py` | Applies a research assistant's reply back into the database — see "Filling in the reference data" below. |
| `QUICKSTART.md` | Standalone install/use walkthrough, bundled into `Export archive and tools`. |
| `docs/` | The three PDF manuals (Installation, User, Technical) and `build_manuals.py`, which regenerates them. Also linked from the GUI's Help menu. |

Requires Python 3.8+. `openpyxl` is only needed for export; `tkinter` only for the
GUI — on most systems it ships with Python, but Debian and Ubuntu split it out
into `python3-tk`. `reportlab` is only needed to regenerate the PDF manuals in
`docs/` (`python3 docs/build_manuals.py`).

## The window

```bash
python3 valves_gui.py
```

Both front ends read and write the same `valves.db`, so use whichever suits the
moment — the GUI for browsing and filling in datasheet figures, the CLI for
quick lookups and scripting. Four tabs:

### Valves

- **Boxes down the left** — click a heading to sort, click a box to filter,
  "All boxes" to clear.
- **Search row** — text, function, base, and the numeric fields, taking the
  same `>20` / `<7` / `>=250` comparisons as the CLI. Searching a type by name
  also pulls in stock of anything cross-referenced as its equivalent (shown
  in blue, labelled which type it's equivalent to) — search `ECF80` and you'll
  see `PCF80` stock too. **Advanced...** opens every field — maker, condition,
  family, confidence, has-datasheet, and the rest of the numeric ratings.
- **Results table** — click a heading to sort, double-click a row to open its
  datasheet. **Amber rows are unconfirmed (inferred); blue rows are
  equivalents pulled in by a search.**
- **Panel on the right** — the type's reference record, editable in place.
  *Save* keeps it inferred; *Save + confirm* marks it confirmed and the row
  turns black — that amber-to-black transition is the progress bar for
  working through the collection. Below it, **Similar types** lists other
  held types with the same function and every shared electrical rating within
  50% — not equivalents, just plausible substitutes with modification (heater
  mismatches are flagged, not filtered out, since a dropping resistor or a
  different supply can usually cover that). Double-click one to look it up.
  *Open datasheet* / *RadioMuseum* / *Web search* look up whatever's selected.
- **Add stock / Take / Move / Delete lot** act on the selected row. *Add stock*
  creates the type automatically if it's new, classifying it as it goes.

### Bases / Sockets

Same idea as the Valves tab, for the sockets/bases themselves rather than the
valves that plug into them — tracked separately since they're not valves.

### Browse

A parametric filter: dropdowns for function/base/family/confidence and
operator+value pickers (`<` `=` `>`) for every numeric rating, all cascading —
picking one narrows what the others offer. A name filter narrows the list as
you type (`3cx`, `PL`, whatever). Click a heading to sort; double-click a
type for a popup showing exactly which boxes hold it and how many in each.

### Repair Bench

For "I've got this valve out of a set I'm fixing — what is it, and what have
I got that could stand in for it?" Type the designation (and optionally which
circuit stage it came from), *Identify*.

If it's already in your database, its reference data loads straight in, **In
stock now** shows anything you hold of that exact type or a listed
equivalent, and **Possible substitutes** lists other held types with the same
function and every shared rating within 50% — the Valves tab's Similar-types
logic, scoped to what's actually in stock. Double-click a substitute to
switch the bench to it.

If it's new to you, *Open datasheet* / *RadioMuseum* / *Web search* work
immediately off the typed name, and *Copy research prompt* puts a
single-type research prompt on the clipboard (same block format Apply
researched data... expects). *Add to database* creates a bare reference
record so there's somewhere to save what you find; *Save* / *Save + confirm*
work exactly as the Valves tab detail panel and immediately refresh the
substitute list with whatever you just entered.

### Tools menu

Collection summary, what still needs data, duplicate candidates, scanning the
datasheet archive; a blank upload template, CSV import, and a CSV-building
prompt for turning someone's own messy records into an import (see "Keeping
it current" below); and the two research-prompt workflows (see "Filling in
the reference data" below) — one for electrical parameters, one for pulling
missing datasheet PDFs into the local archive. **File > Export archive and
tools** zips up the tools, docs, and a fresh snapshot for handing the whole
thing to someone else — see `QUICKSTART.md`.

### Help menu

A task-by-task **User guide** covering all of the above, plus links to open
the three PDF manuals in `docs/` (Installation, User, Technical) in whatever
PDF viewer is installed.

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

## Starting your own collection

The database that ships here is mine. To make it yours:

**Option A — start empty.** Delete the working database and launch the app;
a fresh, empty one is created automatically:

```bash
rm valves.db          # del valves.db on Windows
python3 valves_gui.py
```

**Option B — keep the reference library, clear the stock.** The 253
researched valve types (function, base, heater, ratings) are useful on
their own regardless of whose valves they are — keep that, wipe out my
boxes and quantities:

```bash
python3 -c "
import valvelib as V
con = V.init_db()
for t in ('stock', 'socket', 'sundry', 'box'):
    con.execute(f'DELETE FROM {t}')
con.commit()
n = con.execute('SELECT COUNT(*) FROM valve_type').fetchone()[0]
print('cleared - kept', n, 'reference types')
"
```

Either way, run `python3 snapshot.py` afterward if you want your own fork's
`data/` to reflect the change before committing.

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
designation as it goes. For a whole batch at once, use `import-csv` (or
Tools > Import upload CSV in the GUI) with a file shaped like
`upload_template.csv` — same auto-classification, one row per lot. Tools >
Create upload template writes a blank copy of that CSV ready to fill in; if
your existing records aren't already in that shape, Tools > Generate
CSV-building prompt writes a prompt for any Claude chat that interviews you
(or reads whatever spreadsheet, notes, or photos you describe) and hands back
a ready-to-import CSV.

## Filling in the reference data

Parameters start out **inferred from the type designation** — a guess, not a
datasheet reading. Types are marked `inferred` until confirmed, either by hand:

```bash
python3 valves.py set EL34 --pa 25 --va 800 --gm 11 --mu 11 \
                           --base octal --pins 8 --power-out 25 --confirm
```

or by handing the gap list to a research assistant. In the GUI, Tools >
Generate research prompt... writes a ready-to-paste prompt (same one described
above, aimed at your highest-quantity unconfirmed types) into a text file.
Paste it into Claude, save the reply, then Tools > Apply researched data...
(or `python3 import_researched.py <file> --yes` from the command line) writes
back only what was actually confirmed — a hedged finding ("could not verify",
"plausible") is kept as a lead rather than marked `confirmed`.

Missing the datasheet PDF itself, rather than just the parameters? Tools >
Generate datasheet download prompt... writes a prompt aimed at an agent with
file *and* web access (Claude Code, not a plain chat, since it needs to write
files to disk) — it tries `fetch_datasheets.py` first, then searches further
for whatever's still missing and saves PDFs straight into the local archive.

`--confirm` flips a record to `confirmed`. `python3 valves.py gaps` lists what
still needs attention, ordered by how many you actually hold — so the effort
goes where it's worth spending.

Current coverage: **201 of 253** types are `confirmed`, **243** have a
function and **227** a heater rating. The rest are one-offs and rare types
the naming conventions and the usual archives don't cover.

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
