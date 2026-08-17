#!/usr/bin/env python3
"""
build_manuals.py - generates the three PDF manuals in docs/ from the content
below. Re-run any time the tool changes enough to make them stale:

    python3 docs/build_manuals.py

Requires reportlab (pip install reportlab) - not a runtime dependency of the
tool itself, only needed to regenerate these PDFs.

Layout of this file:
  - styling section: a shared reportlab stylesheet (STYLES) and small helper
    functions (title/h1/h2/h3/p/note/code/bullets/table) that wrap Platypus
    flowable construction so the content functions below can stay readable.
  - build(): assembles a SimpleDocTemplate from a list of flowables and
    writes it to disk.
  - installation_manual() / user_manual() / technical_manual(): each builds
    and returns the full flowable list for one manual. All the actual manual
    prose lives inside these three functions, passed as string arguments to
    the helpers above.
  - main(): builds all three PDFs.
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle,
    PageBreak, ListFlowable, ListItem,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- styling
# Shared ParagraphStyle set used by every helper below and by all three
# manuals, built on top of reportlab's default stylesheet so headings, body
# text, notes, code blocks, bullets, and table cells look consistent across
# documents.

_base = getSampleStyleSheet()

STYLES = {
    "title": ParagraphStyle("title", parent=_base["Title"], fontSize=24,
                            spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Normal"], fontSize=12,
                               textColor=colors.HexColor("#555555"), spaceAfter=28),
    "h1": ParagraphStyle("h1", parent=_base["Heading1"], fontSize=17,
                         spaceBefore=22, spaceAfter=10,
                         textColor=colors.HexColor("#1a1a1a")),
    "h2": ParagraphStyle("h2", parent=_base["Heading2"], fontSize=13,
                         spaceBefore=14, spaceAfter=6,
                         textColor=colors.HexColor("#1a1a1a")),
    "h3": ParagraphStyle("h3", parent=_base["Heading3"], fontSize=11,
                         spaceBefore=10, spaceAfter=4,
                         textColor=colors.HexColor("#333333")),
    "body": ParagraphStyle("body", parent=_base["Normal"], fontSize=10,
                           leading=14, spaceAfter=8, alignment=TA_LEFT),
    "note": ParagraphStyle("note", parent=_base["Normal"], fontSize=9.5,
                           leading=13, spaceAfter=8, leftIndent=10,
                           borderColor=colors.HexColor("#c9c9c9"), borderWidth=0,
                           textColor=colors.HexColor("#444444"),
                           backColor=colors.HexColor("#f4f4f2")),
    "code": ParagraphStyle("code", parent=_base["Code"], fontSize=9,
                           leading=12, backColor=colors.HexColor("#f4f4f2"),
                           leftIndent=8, spaceAfter=10, spaceBefore=2),
    "bullet": ParagraphStyle("bullet", parent=_base["Normal"], fontSize=10,
                             leading=14),
    "caption": ParagraphStyle("caption", parent=_base["Normal"], fontSize=8.5,
                              textColor=colors.HexColor("#777777")),
}


def title(text, subtitle=""):
    """Return the flowables for a document's title block: a Title paragraph,
    plus an optional subtitle paragraph beneath it. Used once per manual."""
    out = [Paragraph(text, STYLES["title"])]
    if subtitle:
        out.append(Paragraph(subtitle, STYLES["subtitle"]))
    return out


def h1(text):
    """Top-level numbered section heading (e.g. "1. Requirements")."""
    return Paragraph(text, STYLES["h1"])


def h2(text):
    """Second-level heading, nested under an h1 section."""
    return Paragraph(text, STYLES["h2"])


def h3(text):
    """Third-level heading, nested under an h2 subsection."""
    return Paragraph(text, STYLES["h3"])


def p(text):
    """Standard body paragraph. text may contain reportlab's mini-HTML markup
    (<b>, <i>, <font face="Courier">, entities) since Paragraph interprets it."""
    return Paragraph(text, STYLES["body"])


def note(text):
    """A callout paragraph prefixed with a bold "Note:" label and shaded
    background, for asides that shouldn't be mistaken for main-flow text."""
    return Paragraph(f"<b>Note:</b> {text}", STYLES["note"])


def code(text):
    """A monospace, shaded block for literal shell commands or code, rendered
    verbatim (no markup interpretation, unlike Paragraph-based helpers)."""
    return Preformatted(text, STYLES["code"])


def bullets(items):
    """A bulleted list flowable from a list of markup strings, one bullet
    per item."""
    return ListFlowable(
        [ListItem(Paragraph(t, STYLES["bullet"]), leftIndent=6) for t in items],
        bulletType="bullet", start="\u2022", leftIndent=14, spaceAfter=10)


_TABLE_HEADER_STYLE = ParagraphStyle("theader", parent=_base["Normal"], fontSize=9,
                                     leading=12, textColor=colors.white,
                                     fontName="Helvetica-Bold")
_TABLE_CELL_STYLE = ParagraphStyle("tcell", parent=_base["Normal"], fontSize=9, leading=12)


def table(rows, col_widths, header=True):
    """Build a styled Table flowable from rows of cell text (rows[0] is the
    header row when header=True). col_widths gives each column's fixed width."""
    # Plain strings in a Table cell render as a single unwrapped line and
    # silently overflow the column - wrap everything in a Paragraph so long
    # cells actually wrap to the given column width.
    wrapped = []
    for i, row in enumerate(rows):
        style = _TABLE_HEADER_STYLE if (header and i == 0) else _TABLE_CELL_STYLE
        wrapped.append([Paragraph(str(cell), style) for cell in row])
    t = Table(wrapped, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8d8d8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c2c2c")))
    t.setStyle(TableStyle(style))
    return t


def build(filename, story):
    """Assemble and write a SimpleDocTemplate PDF from a list of flowables."""
    doc = SimpleDocTemplate(
        os.path.join(HERE, filename), pagesize=LETTER,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        title=filename.replace(".pdf", "").replace("_", " ").title(),
        author="Valve inventory toolkit")
    doc.build(story)
    print(f"wrote {filename}")


# ==========================================================================
# INSTALLATION MANUAL
# ==========================================================================

def installation_manual():
    """Return the Installation Manual's flowables."""
    s = []
    s += title("Valve Inventory", "Installation Manual")
    s.append(p(
        "This covers getting the tool running from nothing - whether you're setting it up "
        "for the first time, or you were handed an exported copy by someone else (see "
        "File &gt; Export archive and tools in the app, or QUICKSTART.md)."))

    s.append(h1("1. Requirements"))
    s.append(bullets([
        "<b>Python 3.8 or later.</b> Check with <font face=\"Courier\">python3 --version</font>.",
        "<b>tkinter</b>, for the desktop window. Ships with most Python installs; on "
        "Debian/Ubuntu it's a separate package: <font face=\"Courier\">sudo apt install "
        "python3-tk</font>.",
        "<b>openpyxl</b>, only if you want to export a spreadsheet snapshot: "
        "<font face=\"Courier\">pip install openpyxl</font>.",
        "<b>reportlab</b>, only if you want to regenerate these manuals: "
        "<font face=\"Courier\">pip install reportlab</font>.",
    ]))
    s.append(note(
        "Nothing else is required at runtime. The database engine (SQLite) is built into "
        "Python's standard library - there is no server to install or configure."))

    s.append(h1("2. Getting the files"))
    s.append(p(
        "The repository is <font face=\"Courier\">GarethDaviesLondon/ValveInventory</font> on "
        "GitHub: <font face=\"Courier\">https://github.com/GarethDaviesLondon/"
        "ValveInventory</font>. Three ways to get a working copy:"))

    s.append(h2("2a. Clone the repository (latest)"))
    s.append(p("Tracks ongoing development on the main branch."))
    s.append(code(
        "git clone https://github.com/GarethDaviesLondon/ValveInventory.git\n"
        "cd ValveInventory"))

    s.append(h2("2b. Download a tagged release (recommended once one exists)"))
    s.append(p(
        "A tagged release is a known-good snapshot rather than whatever main happens to be at "
        "the moment - the first is planned as <b>v1.0</b>. Once it's out:"))
    s.append(bullets([
        "<b>No git needed</b> - open "
        "<font face=\"Courier\">https://github.com/GarethDaviesLondon/ValveInventory/"
        "releases</font>, pick the release (e.g. v1.0), and download its "
        "“Source code (zip)” asset under Assets. Unzip it and follow section 3 "
        "below as normal.",
        "<b>With git</b> - clone just that tag rather than the full history:",
    ]))
    s.append(code(
        "git clone --branch v1.0 --depth 1 \\\n"
        "    https://github.com/GarethDaviesLondon/ValveInventory.git\n"
        "cd ValveInventory"))
    s.append(note(
        "No release has been tagged yet at the time of writing - until v1.0 lands, use 2a "
        "(clone) or ask whoever gave you this manual for their own export (2c)."))

    s.append(h2("2c. You were given an exported .zip"))
    s.append(p(
        "Produced by File &gt; Export archive and tools in the GUI. Just unzip it "
        "anywhere - it's not tied to git."))
    s.append(code("unzip valve_inventory_export.zip -d valve-inventory\ncd valve-inventory"))

    s.append(h1("3. Building the database"))
    s.append(p(
        "The working database, <font face=\"Courier\">valves.db</font>, is never itself "
        "committed or exported - it's a binary SQLite file that would just bloat version "
        "control and can't be diffed. What travels with the project is a text snapshot in "
        "<font face=\"Courier\">data/</font>, which rebuilds it:"))
    s.append(code("python3 snapshot.py --restore"))
    s.append(p(
        "This reads <font face=\"Courier\">data/valves.sql</font> and writes a fresh "
        "<font face=\"Courier\">valves.db</font> next to it. Safe to re-run any time - it "
        "will refuse to overwrite an existing database unless you pass "
        "<font face=\"Courier\">--force</font>."))

    s.append(h1("4. Confirming it worked"))
    s.append(code("python3 test_smoke.py"))
    s.append(p(
        "This runs a fast set of checks - the type-name classifier, a database round-trip, "
        "each CLI command against a scratch copy, and (if <font face=\"Courier\">data/</font> "
        "is present) the restore path itself. It should print "
        "<font face=\"Courier\">all checks passed</font> and exit cleanly. If it doesn't, "
        "see Troubleshooting below before going further."))

    s.append(h1("5. Running it"))
    s.append(h2("Desktop window"))
    s.append(code("python3 valves_gui.py"))
    s.append(h2("Command line"))
    s.append(code("python3 valves.py stats"))
    s.append(p(
        "Both read and write the same <font face=\"Courier\">valves.db</font> - there is no "
        "separate setup for one versus the other."))

    s.append(h1("6. The datasheet archive (optional)"))
    s.append(p(
        "PDF datasheets are not included in a clone or an export - hundreds of megabytes of "
        "third-party files that would swamp the repository. Build your own copy locally:"))
    s.append(code(
        "python3 fetch_datasheets.py --index      # maps the site - slow, run once, resumable\n"
        "python3 fetch_datasheets.py --download   # pulls only the types this database holds\n"
        "python3 valves.py scan                   # links the downloaded files in"))
    s.append(p(
        "The default 2-second delay between requests is deliberate - the source site runs on "
        "donations. Both stages are resumable, so Ctrl-C is always safe. If you'd rather have "
        "Claude do this work (including finding sources beyond that one site), the GUI's "
        "Tools &gt; Generate datasheet download prompt... writes a ready-to-use prompt for "
        "an agent with file and web access, such as Claude Code."))

    s.append(h1("7. Troubleshooting"))
    s.append(table([
        ["Symptom", "Likely cause / fix"],
        ["\u201cNo module named tkinter\u201d",
         "Install the platform tkinter package (e.g. python3-tk on Debian/Ubuntu); it isn't "
         "installable via pip."],
        ["UnicodeDecodeError / UnicodeEncodeError "
         "during restore or CLI output",
         "Windows consoles default to a non-UTF-8 codepage; some collection notes contain "
         "Cyrillic and other non-Latin text. This tool's own scripts already force UTF-8 - if "
         "you hit this in a modified copy, add encoding=\"utf-8\" to the relevant open() call "
         "and sys.stdout.reconfigure(encoding=\"utf-8\") near the top of main()."],
        ["\u201cvalves.db already exists\u201d on restore",
         "Expected safety behaviour - pass --force if you intend to overwrite it, or delete/"
         "rename the existing file first if you're not sure what's in it."],
        ["GUI window closes immediately, no error visible",
         "Run python3 valves_gui.py from a terminal instead of double-clicking the file, so "
         "any traceback stays visible after the window closes."],
        ["openpyxl / reportlab import errors",
         "Both are optional - only needed for File > Export spreadsheet and for rebuilding "
         "these manuals respectively. pip install the missing one, or simply avoid that "
         "feature."],
    ], col_widths=[2.1 * inch, 3.9 * inch]))

    s.append(h1("8. Starting your own collection"))
    s.append(p(
        "The database that ships in this repository is the author's own stock - real box "
        "locations in a real attic, not sample data. To make it yours instead:"))
    s.append(h2("Option A - start empty"))
    s.append(p(
        "Delete the working database and launch the app; a fresh, empty one is created "
        "automatically the moment anything tries to open it:"))
    s.append(code("rm valves.db          # del valves.db on Windows\npython3 valves_gui.py"))
    s.append(h2("Option B - keep the reference library, clear the stock"))
    s.append(p(
        "The 253 researched valve types (function, base, heater, ratings) are useful on their "
        "own regardless of whose valves they are - keep that, wipe out the boxes and "
        "quantities that belong to the original owner's collection:"))
    s.append(code(
        "python3 -c \"\n"
        "import valvelib as V\n"
        "con = V.init_db()\n"
        "for t in ('stock', 'socket', 'sundry', 'box'):\n"
        "    con.execute(f'DELETE FROM {t}')\n"
        "con.commit()\n"
        "n = con.execute('SELECT COUNT(*) FROM valve_type').fetchone()[0]\n"
        "print('cleared - kept', n, 'reference types')\n\""))
    s.append(p(
        "Either way, run <font face=\"Courier\">python3 snapshot.py</font> afterward if you "
        "want your own fork's <font face=\"Courier\">data/</font> to reflect the change before "
        "committing."))

    s.append(h1("9. License and disclaimer"))
    s.append(p(
        "MIT-licensed - see the <font face=\"Courier\">LICENSE</font> file included in this "
        "repository. MIT is about as permissive as licenses get; its one real obligation, "
        "keeping the copyright notice attached, is also what gives it attribution. The data "
        "in <font face=\"Courier\">data/</font> carries its own, separate note in "
        "<font face=\"Courier\">LICENSE</font> - some of the descriptive text there is "
        "third-party material gathered from reference sites, not the author's to relicense."))
    s.append(note(
        "This software is provided without warranty of any kind, express or implied, and you "
        "use it entirely at your own risk. It is hobbyist tooling built for one person's "
        "attic, not a certified reference - treat every “inferred” parameter as a "
        "lead to verify against a real datasheet, not a settled fact, especially before "
        "relying on it for anything involving the lethal voltages a valve amplifier runs at. "
        "By downloading, installing, or running this application, you are confirming that you "
        "have reviewed the source for yourself and that you accept these terms."))

    return s


# ==========================================================================
# USER MANUAL
# ==========================================================================

def user_manual():
    """Return the User Manual's flowables."""
    s = []
    s += title("Valve Inventory", "User Manual")
    s.append(p(
        "A task-by-task walkthrough of the desktop application. For the command-line "
        "equivalent of anything here, see the Technical Manual's command reference, or "
        "README.md."))

    s.append(h1("Overview"))
    s.append(p(
        "The window opens on five tabs, described below, sharing one database. Nothing you "
        "do in one tab is hidden from the others - move stock in the Valves tab and the "
        "Browse tab's counts update the next time you search it."))
    s.append(bullets([
        "<b>Valves</b> - search, edit reference data, add/take/move/delete stock.",
        "<b>Bases / Sockets</b> - the same idea, for the sockets themselves rather than the "
        "valves that plug into them.",
        "<b>Browse</b> - a parametric filter across every held type, for \u201cwhat do I have "
        "that could work here\u201d questions.",
        "<b>Repair Bench</b> - for \u201cI've got this valve out of a set I'm fixing - what is "
        "it, and what have I got that could stand in for it?\u201d",
        "<b>Docs</b> - a general reference library for material that isn't about one specific "
        "type - care-and-feeding guides, base wiring references, and the like.",
    ]))

    s.append(h1("The Valves tab"))
    s.append(h2("Boxes sidebar"))
    s.append(p(
        "Click a box to filter the results to it; click \u201cAll boxes\u201d to clear. Click "
        "a column heading (Box / Types / Qty) to sort, click again to reverse."))
    s.append(h2("Search row"))
    s.append(p(
        "Text, Function, Base, and the numeric fields (Heater V, Pa W, Freq MHz), which "
        "accept comparisons like <font face=\"Courier\">&gt;20</font>, "
        "<font face=\"Courier\">&lt;7</font>, <font face=\"Courier\">&gt;=250</font> as well "
        "as an exact value."))
    s.append(note(
        "Searching a type by name also pulls in stock of anything cross-referenced as its "
        "equivalent - search ECF80 and PCF80 stock shows up too, in blue, labelled which "
        "type it's equivalent to. This is a hint toward substitutes, not a claim they're "
        "necessarily interchangeable in every circuit."))
    s.append(p(
        "<b>Advanced...</b> opens a dialog covering every remaining field - manufacturer, "
        "condition, family, gm, mu, power out, confidence, and whether a datasheet is "
        "linked. It edits the same underlying filters as the quick row, so the two stay in "
        "sync."))
    s.append(h2("Results table"))
    s.append(p(
        "Click a heading to sort. Double-click a row to open its datasheet. "
        "<b>Amber</b> rows have unconfirmed (inferred) parameters; <b>blue</b> rows are "
        "equivalents pulled in by a search."))
    s.append(h2("Detail panel"))
    s.append(p(
        "The selected row's type record, editable in place. <b>Save</b> keeps it inferred; "
        "<b>Save + confirm</b> marks it confirmed and the row turns from amber to black - "
        "that transition is the progress bar for working through the collection."))
    s.append(p(
        "Below the fields, <b>Similar types</b> lists other held types with the same broad "
        "function and every shared electrical rating within 50% - candidates for a "
        "substitute with modification, not verified equivalents. Heater mismatches are "
        "flagged, not filtered out, since a dropping resistor or a different supply can "
        "often cover that. Double-click a suggestion to look it up."))
    s.append(p(
        "<b>Open datasheet</b> opens the local PDF if there is one, otherwise falls back to "
        "an online source - the button itself reads <i>Open datasheet (local)</i> or "
        "<i>Find datasheet (web)</i>, so which one it'll do is clear before you click. "
        "<b>RadioMuseum</b> and <b>Web search</b> run a site-scoped or general search for "
        "whatever's selected. <b>Manage...</b> (<b>Manage information...</b> on the Browse "
        "tab's popup) opens the full document list for a type: the one “primary” sheet that "
        "button opens, plus as many extra datasheets and links as you like - a second "
        "manufacturer's sheet, a forum thread, a project that happens to use this valve. "
        "Upload a file you already have, or paste a URL (no download needed for a link - "
        "it's just recorded). Its <b>Edit parameters...</b> button opens the same field-entry "
        "form as the detail panel, so a Browse-tab research session never needs to switch tabs "
        "to record what a datasheet says."))
    s.append(h2("Toolbar"))
    s.append(p(
        "<b>Add stock</b> creates the type automatically if it's new, classifying it from "
        "its designation. <b>Take</b>, <b>Move</b>, and <b>Delete lot</b> act on the "
        "selected row."))

    s.append(h1("The Bases / Sockets tab"))
    s.append(p(
        "Valve bases and sockets aren't valves, so they're tracked in their own table rather "
        "than mixed into the general sundry catch-all. Same pattern as the Valves tab: search "
        "by base type or box, Add / Take / Move / Delete lot."))

    s.append(h1("The Browse tab"))
    s.append(p(
        "A faceted filter across all held types, closer to a shopping-site filter panel than "
        "a search box."))
    s.append(bullets([
        "<b>Category, Base, Family, Confidence, Variable-mu</b> - dropdowns that "
        "<i>cascade</i>: picking one narrows what the others still offer, so you never land "
        "on an empty combination. Category is a coarser bucket than the raw function text "
        "(Triode, Double triode, Tetrode, Pentode, Triode-pentode, Rectifier, and so on) - "
        "specifically so it's useful as a filter instead of nearly matching one type each.",
        "<b>Numeric ratings</b> (Heater V/A, Va max, Pa max, gm, mu, Power out, Freq max) - "
        "an operator (&lt; = &gt; &lt;= &gt;=) plus a value picked from what's actually "
        "present in the data.",
        "<b>Name contains</b> - narrows the list as you type, e.g. \u201c3cx\u201d or "
        "\u201cPL\u201d.",
    ]))
    s.append(p(
        "Click a heading to sort. <b>Double-click a type</b> for a popup showing its full "
        "reference record, datasheet/web-search buttons, and a box-by-box breakdown of "
        "exactly where and how many you hold."))

    s.append(h1("The Repair Bench tab"))
    s.append(p(
        "The workflow for a valve pulled out of a set on the bench: type its designation "
        "(and, optionally, which circuit stage it came from - IF amp, audio output, "
        "rectifier, and so on), then <b>Identify</b>."))
    s.append(h2("If it's already in your database"))
    s.append(p(
        "Its reference data loads straight into the form on the left. On the right, "
        "<b>In stock now</b> shows anything you already hold of that exact type or a listed "
        "equivalent, and <b>Possible substitutes</b> lists other held types with the same "
        "broad function and every shared rating within 50% - the same candidate logic as the "
        "Valves tab's Similar types, but scoped to what's actually in stock, and with a "
        "held-quantity count. Double-click a substitute to switch the whole bench over to it, "
        "if that turns out to be the more interesting question."))
    s.append(h2("If it's new to you"))
    s.append(p(
        "<b>Open datasheet</b>, <b>RadioMuseum</b>, and <b>Web search</b> work immediately off "
        "the typed designation, before anything is saved. <b>Copy research prompt</b> puts a "
        "ready-to-paste prompt on the clipboard, scoped to just this one type (a faster, "
        "single-item cousin of Tools &gt; Generate research prompt...) - paste it into Claude, "
        "and it comes back in the same block format Apply researched data... expects."))
    s.append(p(
        "<b>Add to database</b> creates a bare reference record (classified from the "
        "designation, no stock attached) so there's somewhere to save findings as you gather "
        "them. <b>Save</b> / <b>Save + confirm</b> work exactly as in the Valves tab detail "
        "panel - and immediately refresh the substitute list on the right using whatever you "
        "just entered, so you can see straight away whether the parameters you found open up "
        "any new candidates from stock."))

    s.append(h1("The Docs tab"))
    s.append(p(
        "A general reference library, for material that isn't about one specific valve type - "
        "a care-and-feeding guide for power tubes, a base wiring reference, anything worth "
        "keeping alongside the collection. <b>Add from file...</b> copies a PDF you already "
        "have into the local archive; <b>Add from URL...</b> just records a link, no download. "
        "Each entry gets a title and an optional abstract - select one to read its abstract in "
        "the pane on the right, and use the filter box to narrow the list as you type."))
    s.append(note(
        "The same title/abstract/file-or-URL idea also applies per type, via the Valves tab's "
        "or Repair Bench's <b>Manage...</b> button - the difference is only whether a "
        "document is filed against one valve type or kept in the general library."))

    s.append(h1("Filling in reference data"))
    s.append(p(
        "New types start out with only what the naming convention can infer - a real "
        "datasheet reading is what actually confirms them. Three ways to close that gap:"))
    s.append(h2("By hand"))
    s.append(p("Edit the fields in the detail panel and Save + confirm, as above."))
    s.append(h2("With Claude - electrical parameters"))
    s.append(p(
        "Tools &gt; Generate research prompt... writes a prompt (for your highest-quantity "
        "unconfirmed types) to a text file. Paste it into any Claude chat, save the reply, "
        "then Tools &gt; Apply researched data.... Only what Claude actually confirmed is "
        "applied - a hedged finding (\u201ccould not verify\u201d, \u201cplausible\u201d) is "
        "kept as a lead rather than marked confirmed, so nothing gets overclaimed."))
    s.append(h2("With Claude - datasheet files"))
    s.append(p(
        "Tools &gt; Generate datasheet download prompt... writes a prompt aimed at an agent "
        "with file and web access (Claude Code, not a plain chat, since it needs to write "
        "files to your disk). It tries the built-in fetcher first, then searches further for "
        "whatever's still missing, and saves PDFs directly into the local archive."))

    s.append(h1("Adding stock in bulk"))
    s.append(p(
        "For more than a few lots at once, skip the Add-stock dialog:"))
    s.append(bullets([
        "<b>Tools &gt; Create upload template...</b> writes a blank CSV with the right "
        "columns, ready to fill in.",
        "<b>Tools &gt; Import upload CSV...</b> reads a filled-in CSV back in - one row per "
        "lot, new types classified automatically, existing types just get more stock.",
        "<b>Tools &gt; Generate CSV-building prompt...</b> writes a prompt for any Claude "
        "chat that interviews you (or reads whatever spreadsheet, notes, or photos you "
        "describe) and hands back a ready-to-import CSV - useful when your existing records "
        "aren't already in this shape.",
    ]))

    s.append(h1("Backup, export, and sharing"))
    s.append(h2("Backup"))
    s.append(p(
        "The database itself isn't the backup - the text snapshot is. Refresh it before "
        "ending a session of changes:"))
    s.append(code("python3 snapshot.py"))
    s.append(p(
        "That's what belongs in version control; it's what a restore rebuilds from."))
    s.append(h2("Export a spreadsheet"))
    s.append(p(
        "File &gt; Export spreadsheet... writes a plain .xlsx for anyone who just wants to "
        "look, not use the tool."))
    s.append(h2("Hand the whole thing to someone else"))
    s.append(p(
        "File &gt; Export archive and tools (.zip)... bundles the code, docs, and a fresh "
        "snapshot into one file, with an option to strip the third-party descriptive text "
        "first (see the Technical Manual's note on that). The recipient unzips it and follows "
        "QUICKSTART.md, which is included."))

    return s


# ==========================================================================
# TECHNICAL MANUAL
# ==========================================================================

def technical_manual():
    """Return the Technical Manual's flowables."""
    s = []
    s += title("Valve Inventory", "Technical Manual")
    s.append(p(
        "Architecture, schema, and internals - for anyone extending the tool, scripting "
        "against the database directly, or just wanting to know how a feature actually "
        "works under the hood."))

    s.append(h1("1. Architecture"))
    s.append(p(
        "One SQLite database, two independent front ends that read and write it directly - "
        "there is no server, no API layer, and no ORM. Both front ends import "
        "<font face=\"Courier\">valvelib.py</font> for the schema and shared logic."))
    s.append(table([
        ["File", "Role"],
        ["valvelib.py", "Schema (SCHEMA string, executed via executescript), "
         "type-name normalisation (norm()), and the naming-convention classifier "
         "(classify())."],
        ["valves.py", "Command-line front end. One cmd_* function per subcommand, dispatched "
         "via argparse."],
        ["valves_gui.py", "Tkinter desktop front end. A single App(ttk.Frame) class holding "
         "four tabs' worth of widgets and handlers."],
        ["build_db.py", "One-off converter from the original 38-tab spreadsheet. Already run; "
         "kept for provenance, not part of normal operation."],
        ["snapshot.py", "Writes/restores the data/ text snapshot that stands in for the "
         "binary database in version control."],
        ["fetch_datasheets.py", "Two-stage, rate-limited crawler/downloader for the local "
         "datasheet archive (frank.pocnet.net only)."],
        ["import_researched.py", "Parses a Claude research reply (block format below) and "
         "applies it to valve_type."],
        ["test_smoke.py", "No framework - a flat script of check()/check_true() calls, exits "
         "non-zero on first failure."],
    ], col_widths=[1.7 * inch, 4.3 * inch]))

    s.append(h1("2. Database schema"))
    s.append(p(
        "Six tables plus one convenience view, declared in "
        "<font face=\"Courier\">valvelib.SCHEMA</font> and created with "
        "<font face=\"Courier\">CREATE TABLE IF NOT EXISTS</font> - so adding a table to the "
        "schema and re-running <font face=\"Courier\">V.init_db()</font> (which both front "
        "ends do on every startup) is enough to migrate an existing database with no separate "
        "migration step."))
    s.append(h2("valve_type - one row per type, the reference library"))
    s.append(p(
        "Primary key <font face=\"Courier\">type_key</font> (normalised: uppercase, "
        "alphanumeric only - see norm() below). Columns: name, function, family, base, pins, "
        "heater_v, heater_a, va_max, pa_max, gm, mu, power_out, freq_max, typical_use, "
        "equivalents (space-separated), datasheet_path, datasheet_url, confidence "
        "(<font face=\"Courier\">inferred</font> | <font face=\"Courier\">confirmed</font>), "
        "notes."))
    s.append(h2("stock - one row per physical lot"))
    s.append(p(
        "type_key (FK to valve_type, ON UPDATE CASCADE), box, qty, manufacturer, condition, "
        "date_added, notes. The box identifier is free text, not an enforced foreign-key "
        "relationship - the separate box table below just carries optional per-box "
        "location/label notes keyed on that same identifier."))
    s.append(h2("socket - one row per lot of bases/sockets"))
    s.append(p(
        "base, box, qty, condition, notes. Split out from sundry deliberately, so a base type "
        "is a first-class, searchable thing rather than free text."))
    s.append(h2("sundry / box"))
    s.append(p(
        "sundry is the general catch-all for non-valve, non-socket items (crystals, "
        "screening cans, chimneys). box holds per-box location/label notes, keyed on the "
        "same free-text box identifier used in stock and socket."))
    s.append(h2("document - extra datasheets, links, and the general reference library"))
    s.append(p(
        "id, type_key (FK to valve_type, nullable), title, abstract, path, url, added. "
        "Deliberately additive rather than a replacement for "
        "<font face=\"Courier\">valve_type.datasheet_path</font>/"
        "<font face=\"Courier\">datasheet_url</font>, which remain the one “primary” "
        "sheet that every existing Open-datasheet code path already knows how to open - this "
        "table only ever adds to that, it's never read by the primary-sheet lookup. Whether a "
        "row is per-type or general-library is entirely down to type_key: NOT NULL puts it in "
        "that type's “Manage...” document list (DatasheetManagerDialog), NULL puts it "
        "in the Docs tab instead. path and url are both optional and independent - a "
        "link-only row (path NULL) is exactly how “note a project that mentions this "
        "valve, without downloading anything” gets recorded."))
    s.append(h2("v_stock (view)"))
    s.append(p(
        "stock LEFT JOIN valve_type, exposing the commonly-needed combined columns (type "
        "name, function, heater_v, pa_max, freq_max, base, datasheet_path) without repeating "
        "the join in every query."))
    s.append(note(
        "The type_key -> stock.type_key foreign key is declared "
        "<font face=\"Courier\">ON UPDATE CASCADE</font>. That matters in practice: renaming "
        "a type_key (e.g. correcting a mis-entered designation) is a single UPDATE on "
        "valve_type, done through a connection with foreign_keys=ON (V.connect() sets this) "
        "- stock rows follow automatically, no manual UPDATE stock needed."))

    s.append(h1("3. Type-name normalisation and classification"))
    s.append(h2("norm(name)"))
    s.append(p(
        "Uppercases, strips a leading JAN/JAN-/CV- service prefix, then strips everything "
        "that isn't A-Z0-9. \u201cjan 7289\u201d \u2192 \u201c7289\u201d; "
        "\u201cPY 4-400\u201d \u2192 \u201cPY4400\u201d. This is the type_key used "
        "everywhere - display names keep their original punctuation in "
        "<font face=\"Courier\">name</font>."))
    s.append(h2("classify(name)"))
    s.append(p(
        "Infers function/heater/family from the designation alone, trying each national "
        "naming convention in turn until one matches: a curated KNOWN table (hand-entered "
        "for designations no rule covers) first, then GEC beam tetrodes (KT-prefix), "
        "European Mullard/Philips codes, British Mazda/Brimar codes, Russian codes, American "
        "RETMA codes, British GEC/Osram codes, then transmitting-type patterns "
        "(4CX/3-500Z-style). Returns whatever it's confident about and leaves the rest blank "
        "- see the code comments for exactly which patterns are accepted and why (several "
        "national schemes collide on the same letter/number patterns, so order and specific "
        "guard conditions matter)."))
    s.append(note(
        "classify() output is always confidence='inferred'. Nothing sets confidence to "
        "confirmed except a human (Save + confirm in the GUI, --confirm on the CLI) or "
        "import_researched.py applying a research result that wasn't hedged."))

    s.append(h1("4. GUI internals worth knowing"))
    s.append(h2("Equivalents-aware search"))
    s.append(p(
        "run_search() builds the normal filtered query, then add_equivalent_rows() checks "
        "whether the Text field names an exact type_key; if so it pulls in stock for every "
        "type_key that either appears in that type's own equivalents field, or has this "
        "type's key in <i>its</i> equivalents field (checked both directions in Python, not "
        "SQL, since equivalents is unstructured free text). Matched rows get a "
        "<font face=\"Courier\">match</font> label and the <font face=\"Courier\">equiv</font> "
        "tree tag."))
    s.append(h2("Similar-types suggestions"))
    s.append(p(
        "find_similar() buckets the current type's function text via function_group() (a "
        "simple first-match keyword scan against valvelib.FUNCTION_GROUPS), then scans every "
        "other held type in the same bucket, requiring every field both types have a value "
        "for (va_max, pa_max, gm, mu, power_out, freq_max) to be within "
        "SIMILAR_TOLERANCE (50%) of the reference. Heater is deliberately excluded from the "
        "match test and checked separately as a flag - a different heater rating doesn't "
        "rule out a substitute, it just needs a note."))
    s.append(h2("Browse tab - Category vs. Function"))
    s.append(p(
        "The raw function text is specific enough that almost every type has a unique value, "
        "which makes it useless as a browse facet. browse_category() maps it to a coarser, "
        "purpose-built bucket list (BROWSE_CATEGORIES) instead - compound types are checked "
        "before the simpler categories they'd otherwise match as a substring (\u201ctriode-"
        "pentode\u201d before \u201ctriode\u201d). variable_mu is a second derived, orthogonal "
        "flag (checks for \u201cvariable-mu\u201d / \u201cremote cutoff\u201d wording), since "
        "that property cuts across pentode and tetrode rather than being its own category."))
    s.append(p(
        "Because category/variable_mu aren't real columns, the whole Browse tab filters in "
        "Python over the full (small, ~250-row) type list rather than building SQL per field "
        "- see pb_load_all() / pb_matches() / pb_refresh_dropdowns(). At this scale that's "
        "faster to reason about than parallel SQL and Python category logic, and cascading "
        "dropdown options (pb_matches(..., exclude=field)) fall out of the same predicate "
        "function for free."))
    s.append(h2("Repair Bench - composition over duplication"))
    s.append(p(
        "Nothing about identifying an unknown valve or proposing a substitute is new logic - "
        "the tab (rb_* methods) is built entirely from pieces the other tabs already needed: "
        "find_similar() for substitute candidates (reused as-is, then filtered to held_qty &gt; "
        "0 - a substitute you don't have isn't useful mid-repair), do_open_sheet(row) / "
        "do_lookup(site, row) for datasheet and web lookups (both already took an optional "
        "explicit row dict rather than always reading the Valves tab's selection, precisely so "
        "other tabs could call them), and the same bidirectional equivalents scan used by the "
        "Valves tab's search (factored out here as rb_find_matches() rather than shared "
        "directly, since the Valves tab version is itself embedded in a larger SQL query "
        "builder). save_type() was split into apply_type_fields(key, field_vars, notes_widget, "
        "confirm) plus a thin wrapper specifically so Repair Bench's Save button could reuse "
        "the exact same validate-and-write logic against its own, separate form widgets."))

    s.append(h1("5. The research/import pipeline"))
    s.append(p(
        "Both the electrical-parameters prompt and the datasheet-download prompt are "
        "generated from the live gap list at the moment you ask for them (Tools menu), not "
        "hard-coded - re-running them later reflects whatever's still unconfirmed then."))
    s.append(h2("Expected reply format"))
    s.append(code(
        "TYPE_NAME\n"
        "function:\n"
        "base:\n"
        "pins:\n"
        "heater_v:\n"
        "heater_a:\n"
        "va_max:\n"
        "pa_max:\n"
        "gm:\n"
        "mu:\n"
        "power_out:\n"
        "freq_max:\n"
        "typical_use:\n"
        "equivalents:\n"
        "source_url:\n"
        "confidence_note:\n"
        "---"))
    s.append(p(
        "import_researched.py's parse_blocks() splits on the "
        "<font face=\"Courier\">---</font> separator, normalises the first line of each block "
        "through the same norm() used everywhere else, and pulls a bare number out of each "
        "numeric field with a permissive regex (so \u201c250 V\u201d or \u201c~250\u201d "
        "still parses). A block whose only non-blank field is equivalents is skipped "
        "entirely, on the basis that \u201cwe already knew that\u201d isn't a research "
        "result worth recording."))
    s.append(h2("Confirmed vs. lead-only"))
    s.append(p(
        "apply_records() checks confidence_note against a fixed list of hedge phrases "
        "(HEDGE_WORDS: \u201ccould not\u201d, \u201clow confidence\u201d, \u201cplausible\u201d, "
        "\u201cunconfirmed\u201d, and similar). If any match, the fields are still written - "
        "the data is a genuine lead worth keeping - but confidence stays "
        "<font face=\"Courier\">inferred</font> rather than flipping to "
        "<font face=\"Courier\">confirmed</font>. This is the same policy applied by hand "
        "throughout this collection's own research pass; see the notes field on any type "
        "for a worked example."))

    s.append(h1("6. CLI command reference"))
    s.append(table([
        ["Command", "Purpose"],
        ["box BOX", "List a box's contents."],
        ["find TYPE", "Which boxes hold a type (follows equivalents)."],
        ["show TYPE", "Full reference record for a type."],
        ["search --function .. --heater .. --pa ..", "Parametric search; numeric flags take "
         "a bare value or a >, <, >=, <= comparison."],
        ["add TYPE --box N [--qty --maker --condition --notes]", "Add stock; creates the "
         "type automatically if new."],
        ["import-csv FILE", "Bulk-add stock from a CSV (see upload_template.csv)."],
        ["take TYPE [--qty --box]", "Remove stock you've used."],
        ["move TYPE --frm A --to B", "Move a type between boxes."],
        ["bases [--base --box]", "List valve base/socket stock."],
        ["sock-add / sock-take / sock-move", "Same idea as add/take/move, for bases/sockets."],
        ["docs [--type TYPE]", "List reference documents - the general library by default, or "
         "one type's primary datasheet plus its extra documents/links with --type."],
        ["set TYPE --pa .. --va .. --confirm", "Edit a type's reference parameters; "
         "--confirm marks it confirmed."],
        ["merge SRC DST [--yes]", "Fold one type into another - moves stock, records SRC as "
         "an equivalent of DST. Dry-run without --yes."],
        ["dupes", "Candidate duplicate type pairs, for review before merge."],
        ["scan [--archive]", "Link local datasheet files into the database by filename."],
        ["sheet TYPE [--open]", "Locate (and optionally open) a type's local datasheet."],
        ["gaps [--limit]", "What still needs data, ordered by quantity held."],
        ["stats", "Collection summary."],
        ["export [path]", "Write an .xlsx snapshot (requires openpyxl)."],
    ], col_widths=[2.5 * inch, 3.5 * inch]))

    s.append(h1("7. Version control and the snapshot design"))
    s.append(p(
        "<font face=\"Courier\">valves.db</font> is gitignored. SQLite databases are binary "
        "blobs - git can store them but every single-row edit rewrites the whole file, so "
        "diffs are meaningless and history is bloated. snapshot.py writes the same content as "
        "plain CSV (one file per table) plus a full SQL dump "
        "(<font face=\"Courier\">valves.sql</font>, via <font face=\"Courier\">con."
        "iterdump()</font>), all under <font face=\"Courier\">data/</font>. That's what's "
        "actually committed - readable diffs for every change to the collection, and a "
        "restore path that doesn't depend on the SQLite file format being stable across "
        "versions."))
    s.append(note(
        "iterdump() emits tables in alphabetical order, which lists stock rows before "
        "valve_type exists. restore() explicitly runs with foreign_keys=OFF while loading "
        "the dump for exactly this reason, then reports (rather than silently ignoring) any "
        "row that fails PRAGMA foreign_key_check afterward."))

    s.append(h1("8. Privacy note on distributing this data"))
    s.append(p(
        "The typical_use and notes fields carry descriptive text originally gathered from "
        "r-type.org during the original conversion - not something to republish freely. "
        "snapshot.py --strip-notes (and the equivalent checkbox in File &gt; Export archive "
        "and tools) omits those two fields from the export while leaving every classification, "
        "parameter, and box location intact. Datasheet PDFs are gitignored and never included "
        "in an export for the same reason - they're third-party files, meant to be rebuilt "
        "locally by whoever needs them."))

    s.append(h1("9. Extending the tool"))
    s.append(bullets([
        "<b>New reference field</b> - add the column to SCHEMA in valvelib.py, then to "
        "TYPE_FIELDS in valves_gui.py (drives the detail-panel form) and ALL_FIELDS in "
        "import_researched.py if research prompts should be able to fill it. No migration "
        "step needed - CREATE TABLE IF NOT EXISTS plus ALTER TABLE-free additive columns "
        "would need a small ALTER TABLE ADD COLUMN in init_db() if adding to an *existing* "
        "table; the tables here were designed with the fields we currently use, so extending "
        "one is the one schema change that isn't fully automatic.",
        "<b>New CLI command</b> - one cmd_*(con, a) function in valves.py plus an "
        "add_parser() block; follow an existing command for the pattern.",
        "<b>New GUI tab</b> - add a _build_x_tab(root) method, call it from App.__init__ "
        "alongside the existing four, and give it its own prefixed method names (px_*) to "
        "avoid colliding with the other tabs' state.",
    ]))

    return s


def main():
    """Build all three manual PDFs."""
    build("INSTALLATION_MANUAL.pdf", installation_manual())
    build("USER_MANUAL.pdf", user_manual())
    build("TECHNICAL_MANUAL.pdf", technical_manual())


if __name__ == "__main__":
    main()
