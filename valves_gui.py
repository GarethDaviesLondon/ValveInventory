#!/usr/bin/env python3
"""
valves_gui.py - desktop front end for the valve inventory.

Same database and same library as valves.py; this is only a different way in.
Run with:  python3 valves_gui.py [--db valves.db] [--archive datasheets]

Layout of this file, top to bottom:
  - module-level constants (treeview column specs, form-field specs, search
    tuning) and small pure helper functions used by more than one tab.
  - dialog classes: FormDialog (generic modal add/edit form), TextWindow
    (read-only scrollable text popup, used for reports and the user guide),
    TypeDetailWindow (Browse tab's box-breakdown popup).
  - App(ttk.Frame): the single main-window class. It builds a ttk.Notebook
    with four tabs, each with its own _build_*_tab() method and its own
    family of handler methods, grouped by prefix and by a comment banner
    in this file:
      Valves tab        - plain names (run_search, load_type, save_type, ...)
      Bases/Sockets tab - sock_* / do_sock_* names
      Browse tab        - pb_* names (parametric/faceted browser)
      Repair Bench tab  - rb_* names (identify + find substitutes + apply
                          pasted research results)
  - main(): argument parsing and Tk startup.

valves_gui.py and valves.py (the CLI) both read/write the same valves.db via
valvelib.py, and both can invoke import_researched.py to apply Claude-sourced
research results - so a change to the schema or to that shared parsing logic
affects both front ends.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
import tkinter as tk
import urllib.parse
import webbrowser
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

PAD = 8

# Valves tab results Treeview columns: (data key, header text, pixel width).
STOCK_COLS = [
    ("box", "Box", 50), ("type", "Type", 100), ("match", "Match", 90), ("qty", "Qty", 42),
    ("manufacturer", "Maker", 88), ("condition", "Condition", 92),
    ("base", "Base", 64), ("function", "Function", 190), ("heater_v", "Htr V", 48),
    ("heater_a", "Htr A", 48), ("pa_max", "Pa W", 46), ("sheet", "Sheet", 44),
]

# Keys that mirror the quick-search row; the advanced dialog edits the same
# StringVars so the two stay in sync instead of filtering twice.
ADV_QUICK_KEYS = {"text", "function", "base", "heater_v", "pa_max", "freq_max"}

# Advanced search: comparison-style fields take '>20' / '<7' / '6.3' like the
# quick-search numeric boxes; the rest are substring matches or a fixed choice.
ADV_FIELDS = [
    ("text", "Text", str), ("function", "Function", str), ("base", "Base", str),
    ("heater_v", "Heater V (e.g. 6.3)", str),
    ("pa_max", "Pa max W (e.g. >20)", str), ("freq_max", "Freq max MHz (e.g. >100)", str),
    ("maker", "Manufacturer", str), ("condition", "Condition", str),
    ("family", "Family", str), ("heater_a", "Heater A (e.g. >0.2)", str),
    ("va_max", "Va max V (e.g. >250)", str), ("gm", "gm mA/V (e.g. >5)", str),
    ("mu", "mu (e.g. >20)", str), ("power_out", "Power out W (e.g. >5)", str),
    ("equivalents", "Equivalents", str),
    ("confidence", "Confidence", ["", "inferred", "confirmed"]),
    ("has_sheet", "Has datasheet", ["", "yes", "no"]),
]

SOCKET_COLS = [
    ("box", "Box", 60), ("base", "Base", 140), ("qty", "Qty", 50),
    ("condition", "Condition", 110), ("notes", "Notes", 260),
]

# Parametric Browser tab: plain dropdown (equality) for categorical fields,
# operator+value dropdown for numeric ones. Both kinds of dropdown cascade -
# their option lists are recomputed from what the *other* active filters
# still allow, like a faceted product filter.
#
# "category" and "variable_mu" aren't real columns - the raw `function` text
# is specific enough that almost every type gets its own value ("triode
# pentode (video output)" vs "triode-pentode (audio driver plus output)"),
# which makes it useless as a browse facet. These are derived, coarser
# buckets computed per row instead - see browse_category()/is_variable_mu().
PB_CAT_FIELDS = [("category", "Category"), ("base", "Base"), ("family", "Family"),
                  ("confidence", "Confidence"), ("variable_mu", "Variable-mu")]
PB_NUM_FIELDS = [("heater_v", "Heater V"), ("heater_a", "Heater A"), ("va_max", "Va max"),
                  ("pa_max", "Pa max"), ("gm", "gm"), ("mu", "mu"),
                  ("power_out", "Power out"), ("freq_max", "Freq max")]
PB_OPS = ["", "=", ">", "<", ">=", "<="]

BROWSE_COLS = [
    ("name", "Type", 90), ("category", "Category", 110), ("function", "Function", 170),
    ("base", "Base", 90), ("heater_v", "Htr V", 48), ("heater_a", "Htr A", 48),
    ("va_max", "Va", 55), ("pa_max", "Pa", 50), ("power_out", "P.out", 55),
    ("freq_max", "Freq", 55), ("qty", "Qty held", 60),
]

# Checked in order - compound/combination types must come before the plain
# categories they'd otherwise also match as a substring (e.g. "triode-pentode"
# has to be tested before "triode" and before "pentode").
BROWSE_CATEGORIES = [
    ("triode-pentode", ["triode-pentode", "triode pentode", "triode + pentode"]),
    ("triode-heptode", ["triode-heptode", "triode heptode"]),
    ("triode-hexode", ["triode-hexode", "triode hexode"]),
    ("diode-triode", ["diode triode", "diode-triode"]),
    ("diode-pentode", ["diode-pentode", "diode pentode", "diode-tetrode"]),
    ("double diode", ["double diode"]),
    ("double triode", ["double triode", "twin triode", "dual triode"]),
    ("beam tetrode", ["beam tetrode", "beam power"]),
    ("tetrode", ["tetrode"]),
    ("pentode", ["pentode"]),
    ("triode", ["triode"]),
    ("rectifier", ["rectifier", "efficiency diode", "booster diode", "switching diode"]),
    ("diode", ["diode"]),
    ("frequency changer", ["heptode", "hexode", "octode", "frequency changer"]),
    ("stabiliser", ["stabiliser", "stabilizer", "voltage reference"]),
    ("indicator", ["tuning indicator", "magic eye", "nixie", "vfd", "vacuum fluorescent"]),
    ("microwave/klystron", ["klystron", "microwave", "planar triode"]),
    ("CRT", ["cathode ray tube"]),
]

VARIABLE_MU_HINTS = ("variable-mu", "variable mu", "remote cutoff", "remote-cutoff", "vari-mu")


def browse_category(text):
    """Classify a type's function text into a coarse Browse-tab category
    by matching keywords against BROWSE_CATEGORIES (checked in order, so
    compound types match before the plain categories they contain). Returns
    None for empty text, "other" if nothing matches."""
    if not text:
        return None
    t = text.lower()
    for label, keywords in BROWSE_CATEGORIES:
        if any(kw in t for kw in keywords):
            return label
    return "other"


def is_variable_mu(row):
    """True if row's function/typical_use text mentions variable-mu /
    remote-cutoff behaviour (see VARIABLE_MU_HINTS)."""
    text = f"{row.get('function') or ''} {row.get('typical_use') or ''}".lower()
    return any(k in text for k in VARIABLE_MU_HINTS)


def compare_op(a, op, b):
    """Apply a comparison operator given as a string ('=', '>', '<', '>=',
    '<='); an unrecognised op (including "") is treated as always true."""
    if op == "=":
        return a == b
    if op == ">":
        return a > b
    if op == "<":
        return a < b
    if op == ">=":
        return a >= b
    if op == "<=":
        return a <= b
    return True

TYPE_FIELDS = [
    ("function", "Function", str), ("base", "Base", str), ("pins", "Pins", int),
    ("heater_v", "Heater V", float), ("heater_a", "Heater A", float),
    ("va_max", "Va max V", float), ("pa_max", "Pa max W", float),
    ("gm", "gm mA/V", float), ("mu", "mu", float),
    ("power_out", "Power out W", float), ("freq_max", "Freq max MHz", float),
    ("equivalents", "Equivalents", str), ("typical_use", "Typical use", str),
]

# These two routinely run to a full sentence or more (typical_use) or a
# handful of designations (equivalents) - a single-line Entry just hides
# most of the content, so they get a wrapped, scrollable Text box instead.
# field_vars dicts end up holding a mix of tk.StringVar (most fields) and
# tk.Text (these two); get_field_value()/set_field_value() abstract over both.
MULTILINE_FIELDS = {"equivalents", "typical_use"}


def get_field_value(widget):
    """Read a form field's current value, whether it's a StringVar-backed
    Entry/Combobox or a multiline tk.Text widget (see MULTILINE_FIELDS)."""
    if isinstance(widget, tk.Text):
        return widget.get("1.0", "end").strip()
    return widget.get().strip()


def set_field_value(widget, value):
    """Write value into a form field, handling both tk.Text widgets and
    StringVar-backed widgets (the counterpart to get_field_value)."""
    if isinstance(widget, tk.Text):
        widget.delete("1.0", "end")
        if value:
            widget.insert("1.0", str(value))
    else:
        widget.set("" if value is None else str(value))


# Fields compared when looking for a substitute with a similar electrical
# profile - heater is deliberately excluded (any heater might do, with a
# dropping resistor or different supply) but checked separately for a flag.
SIMILAR_FIELDS = ("va_max", "pa_max", "gm", "mu", "power_out", "freq_max")
SIMILAR_TOLERANCE = 0.5


def function_group(text):
    """Map a type's function text to one of valvelib's FUNCTION_GROUPS
    buckets by keyword match, or None if nothing matches / text is empty."""
    if not text:
        return None
    t = text.lower()
    for label, keywords in V.FUNCTION_GROUPS:
        if any(kw in t for kw in keywords):
            return label
    return None


def parse_cmp(expr):
    """Parse a comparison expression like '>20', '<=7', or a bare number
    into an (operator, value) pair (operator defaults to '='). Returns
    None if expr doesn't match that shape."""
    m = re.match(r"^\s*(>=|<=|>|<|=)?\s*([\d.]+)\s*$", str(expr))
    if not m:
        return None
    return (m.group(1) or "="), float(m.group(2))


# --------------------------------------------------------------------------
# Dialogs
# --------------------------------------------------------------------------

class FormDialog(tk.Toplevel):
    """Small modal form. fields = [(key, label, default, kind)]"""

    def __init__(self, parent, title, fields, ok_label="OK"):
        """Build the form (one Entry or Combobox per field), center it under
        parent, then block via wait_window until OK or Cancel is chosen.
        fields is [(key, label, default, kind)] where kind is int/float/str
        for a plain Entry or a list of choices for a Combobox. Result is
        left in self.result (a dict) on OK, or None if cancelled."""
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.result = None
        self._vars = {}

        frm = ttk.Frame(self, padding=PAD * 2)
        frm.grid(sticky="nsew")
        for i, (key, label, default, kind) in enumerate(fields):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", pady=3, padx=(0, PAD))
            var = tk.StringVar(value="" if default is None else str(default))
            self._vars[key] = (var, kind)
            if isinstance(kind, list):
                w = ttk.Combobox(frm, textvariable=var, values=kind, width=28)
            else:
                w = ttk.Entry(frm, textvariable=var, width=30)
            w.grid(row=i, column=1, sticky="ew", pady=3)
            if i == 0:
                w.focus_set()

        btns = ttk.Frame(frm)
        btns.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(PAD * 2, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=(PAD, 0))
        ttk.Button(btns, text=ok_label, command=self._ok).pack(side="right")
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + 120
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.grab_set()
        self.wait_window(self)

    def _ok(self):
        """Collect and validate entered values into self.result, coercing
        int/float fields and showing an error dialog (without closing) if a
        value doesn't parse; empty fields become None."""
        out = {}
        for key, (var, kind) in self._vars.items():
            s = var.get().strip()
            if not s:
                out[key] = None
                continue
            if kind in (int, float):
                try:
                    out[key] = kind(s)
                except ValueError:
                    messagebox.showerror("Invalid value",
                                         f"{key} must be a number", parent=self)
                    return
            else:
                out[key] = s
        self.result = out
        self.destroy()


class TextWindow(tk.Toplevel):
    """Read-only scrollable text popup, used for reports and the user guide."""

    def __init__(self, parent, title, body, wrap="none", proportional=False):
        """Show body as read-only text in a new Toplevel positioned near
        parent. wrap is passed straight to the Text widget ("none" for
        preformatted reports, "word" for prose); proportional selects a
        proportional font instead of the default fixed-width one."""
        super().__init__(parent)
        self.title(title)
        self.geometry("640x540")
        self.transient(parent)
        txt = tk.Text(self, wrap=wrap, font="TkDefaultFont" if proportional else "TkFixedFont",
                      borderwidth=0, padx=PAD, pady=PAD)
        sb = ttk.Scrollbar(self, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        txt.insert("1.0", body)
        txt.configure(state="disabled")
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx() + 90}+{parent.winfo_rooty() + 60}")


# Reference fields shown in TypeDetailWindow's info block, in display order.
DETAIL_FIELDS = [
    ("function", "Function", ""), ("base", "Base", ""), ("pins", "Pins", ""),
    ("heater_v", "Heater V", " V"), ("heater_a", "Heater A", " A"),
    ("va_max", "Va max", " V"), ("pa_max", "Pa max", " W"), ("gm", "gm", " mA/V"),
    ("mu", "mu", ""), ("power_out", "Power out", " W"), ("freq_max", "Freq max", " MHz"),
]


class TypeDetailWindow(tk.Toplevel):
    """Box-breakdown popup (Browse tab, double-click a type) - shown alongside
    the type's reference data and the same datasheet/web lookups the Valves
    tab detail panel offers, since a browse result raises the same "what is
    this and where do I read more" question a search result does."""

    def __init__(self, app, t, box_rows):
        """Build the popup for valve_type row `t`, given its stock rows (box_rows)."""
        super().__init__(app.master)
        self.app = app
        self.row = dict(t)
        self.row["type"] = self.row["name"]
        self.title(f"{t['name']} - reference & stock")
        self.geometry("560x560")
        self.transient(app.master)

        top = ttk.Frame(self, padding=(PAD, PAD, PAD, 0))
        top.pack(fill="x")
        ttk.Label(top, text=t["name"], font=("TkDefaultFont", 14, "bold")).pack(side="left")
        ttk.Label(top, text=f"  [{t['confidence']}]", foreground="#666").pack(side="left")
        ttk.Button(top, text="Web search", command=lambda: self._lookup()).pack(side="right")
        ttk.Button(top, text="RadioMuseum",
                  command=lambda: self._lookup("radiomuseum.org")).pack(side="right", padx=(0, 6))
        ttk.Button(top, text="Open datasheet", command=self._open_sheet).pack(side="right", padx=(0, 6))

        info = tk.Text(self, height=11, wrap="word", font=("TkDefaultFont", 9),
                       padx=PAD, pady=6, borderwidth=0, background=self.cget("background"))
        info.pack(fill="x", padx=PAD, pady=(PAD, 0))
        lines = []
        for key, label, unit in DETAIL_FIELDS:
            if t[key] is not None:
                lines.append(f"{label:<12} {t[key]}{unit}")
        if t["equivalents"]:
            lines.append(f"{'Equivalents':<12} {t['equivalents']}")
        if t["typical_use"]:
            lines += ["", t["typical_use"]]
        if t["notes"]:
            lines += ["", f"Notes: {t['notes'][:600]}"]
        if not lines:
            lines = ["No reference data yet."]
        info.insert("1.0", "\n".join(lines))
        info.configure(state="disabled")

        total = sum(r["qty"] for r in box_rows)
        ttk.Label(self, text=f"Box breakdown - {total} held across {len(box_rows)} box(es)",
                 foreground="#666").pack(anchor="w", padx=PAD, pady=(PAD, 2))
        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        tree = ttk.Treeview(mid, columns=("box", "qty", "maker", "condition"),
                            show="headings", height=8)
        for key, label, width in (("box", "Box", 60), ("qty", "Qty", 50),
                                  ("maker", "Maker", 140), ("condition", "Condition", 120)):
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor="e" if key == "qty" else "w")
        vs = ttk.Scrollbar(mid, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vs.set)
        tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="left", fill="y")
        for r in box_rows:
            tree.insert("", "end", values=(r["box"], r["qty"], r["manufacturer"] or "",
                                           r["condition"] or ""))

        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        self.geometry(f"+{app.master.winfo_rootx() + 100}+{app.master.winfo_rooty() + 80}")

    def _open_sheet(self):
        """Delegate to the App's Open datasheet action for this popup's type."""
        self.app.do_open_sheet(self.row)

    def _lookup(self, site=None):
        """Delegate to the App's web-lookup action for this popup's type."""
        self.app.do_lookup(site, self.row)


# --------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------

class App(ttk.Frame):
    """The whole desktop window: a ttk.Notebook with four tabs (Valves, Bases
    / Sockets, Browse, Repair Bench) sharing one database connection. Each
    tab has its own _build_*_tab() constructor and a prefixed set of handler
    methods (plain names for Valves, sock_* / pb_* / rb_* for the other
    three) to keep their state and callbacks from colliding."""

    def __init__(self, master, db, archive):
        """Open `db`, build the menu and all four tabs, and populate them."""
        super().__init__(master, padding=PAD)
        self.master = master
        self.dbpath = db
        self.archive = archive
        self.con = V.init_db(db)
        self.current_type = None
        self.sort_state = {}
        self.box_sort_state = {}
        self.box_rows = []
        self.adv = {}
        self.sock_rows = []
        self.sock_sort_state = {}
        self.rb_current_key = None

        master.title(f"Valve inventory - {os.path.basename(db)}")
        master.geometry("1280x780")
        master.minsize(1000, 620)
        self.pack(fill="both", expand=True)

        self._build_menu()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        valves_tab = ttk.Frame(self.nb, padding=PAD)
        bases_tab = ttk.Frame(self.nb, padding=PAD)
        browse_tab = ttk.Frame(self.nb, padding=PAD)
        bench_tab = ttk.Frame(self.nb, padding=PAD)
        self.nb.add(valves_tab, text="Valves")
        self.nb.add(bases_tab, text="Bases / Sockets")
        self.nb.add(browse_tab, text="Browse")
        self.nb.add(bench_tab, text="Repair Bench")
        self._build_valves_tab(valves_tab)
        self._build_bases_tab(bases_tab)
        self._build_browse_tab(browse_tab)
        self._build_bench_tab(bench_tab)
        self.refresh_boxes()
        self.run_search()
        self.run_sock_search()
        self.pb_run_search()

    # ---------------------------------------------------------------- chrome

    def _build_menu(self):
        """Build the File/Tools/Help menu bar and attach it to the root window."""
        m = tk.Menu(self.master)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label="Export spreadsheet...", command=self.do_export)
        f.add_command(label="Export archive and tools (.zip)...", command=self.do_export_archive)
        f.add_command(label="Open database...", command=self.do_open_db)
        f.add_separator()
        f.add_command(label="Quit", command=self.master.destroy)
        m.add_cascade(label="File", menu=f)

        t = tk.Menu(m, tearoff=0)
        t.add_command(label="Collection summary", command=self.do_stats)
        t.add_command(label="What needs data", command=self.do_gaps)
        t.add_command(label="Possible duplicate types", command=self.do_dupes)
        t.add_separator()
        t.add_command(label="Scan datasheet archive", command=self.do_scan)
        t.add_command(label="Set archive folder...", command=self.do_set_archive)
        t.add_separator()
        t.add_command(label="Create upload template...", command=self.do_create_upload_template)
        t.add_command(label="Import upload CSV...", command=self.do_import_csv)
        t.add_command(label="Generate CSV-building prompt...", command=self.do_generate_csv_prompt)
        t.add_separator()
        t.add_command(label="Generate research prompt...", command=self.do_generate_prompt)
        t.add_command(label="Generate datasheet download prompt...",
                      command=self.do_generate_download_prompt)
        t.add_command(label="Apply researched data...", command=self.do_apply_research)
        m.add_cascade(label="Tools", menu=t)

        h = tk.Menu(m, tearoff=0)
        h.add_command(label="User guide", command=self.do_help_guide)
        h.add_separator()
        h.add_command(label="Installation manual (PDF)",
                      command=lambda: self.do_open_manual("INSTALLATION_MANUAL.pdf"))
        h.add_command(label="User manual (PDF)",
                      command=lambda: self.do_open_manual("USER_MANUAL.pdf"))
        h.add_command(label="Technical manual (PDF)",
                      command=lambda: self.do_open_manual("TECHNICAL_MANUAL.pdf"))
        h.add_separator()
        h.add_command(label="About", command=self.do_about)
        m.add_cascade(label="Help", menu=h)

        self.master.config(menu=m)

    def _build_valves_tab(self, root):
        """Build the Valves tab: boxes sidebar, search row, results table,
        and the type detail/edit panel, into `root`."""
        # ---- toolbar ----
        bar = ttk.Frame(root)
        bar.pack(fill="x", pady=(0, PAD))
        ttk.Button(bar, text="Add stock", command=self.do_add).pack(side="left")
        ttk.Button(bar, text="Take", command=self.do_take).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Move", command=self.do_move).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Delete lot", command=self.do_delete).pack(side="left", padx=(6, 0))

        # ---- filter row ----
        filt = ttk.LabelFrame(root, text="Search", padding=PAD)
        filt.pack(fill="x", pady=(0, PAD))

        self.v_text = tk.StringVar()
        self.v_function = tk.StringVar()
        self.v_base = tk.StringVar()
        self.v_heater = tk.StringVar()
        self.v_pa = tk.StringVar()
        self.v_freq = tk.StringVar()

        specs = [("Text", self.v_text, 20), ("Function", self.v_function, 18),
                 ("Base", self.v_base, 12), ("Heater V", self.v_heater, 8),
                 ("Pa W", self.v_pa, 8), ("Freq MHz", self.v_freq, 8)]
        for i, (label, var, w) in enumerate(specs):
            ttk.Label(filt, text=label).grid(row=0, column=i * 2, sticky="e", padx=(0 if i == 0 else PAD, 4))
            e = ttk.Entry(filt, textvariable=var, width=w)
            e.grid(row=0, column=i * 2 + 1, sticky="w")
            e.bind("<Return>", lambda ev: self.run_search())
        ttk.Label(filt, text="(numeric fields accept  >20  <7  >=250)",
                  foreground="#666").grid(row=1, column=0, columnspan=8, sticky="w", pady=(6, 0))
        btns = ttk.Frame(filt)
        btns.grid(row=0, column=12, padx=(PAD * 2, 0))
        ttk.Button(btns, text="Search", command=self.run_search).pack(side="left")
        ttk.Button(btns, text="Clear", command=self.clear_filters).pack(side="left", padx=(6, 0))
        self.adv_btn = ttk.Button(btns, text="Advanced...", command=self.do_advanced_search)
        self.adv_btn.pack(side="left", padx=(6, 0))

        # ---- three panes ----
        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True)

        # boxes sidebar
        left = ttk.Frame(panes)
        ttk.Label(left, text="Boxes").pack(anchor="w")
        self.boxlist = ttk.Treeview(left, columns=("types", "qty"), height=12)
        self.boxlist.heading("#0", text="Box", command=lambda: self.sort_boxes("box"))
        self.boxlist.heading("types", text="Types", command=lambda: self.sort_boxes("types"))
        self.boxlist.heading("qty", text="Qty", command=lambda: self.sort_boxes("qty"))
        self.boxlist.column("#0", width=90)
        self.boxlist.column("types", width=48, anchor="e")
        self.boxlist.column("qty", width=58, anchor="e")
        self.boxlist.pack(fill="both", expand=True, pady=(4, 0))
        self.boxlist.bind("<<TreeviewSelect>>", self.on_box_select)
        panes.add(left, weight=0)

        # results
        mid = ttk.Frame(panes)
        self.tree = ttk.Treeview(mid, columns=[c[0] for c in STOCK_COLS],
                                 show="headings", selectmode="browse", height=12)
        for key, label, width in STOCK_COLS:
            self.tree.heading(key, text=label, command=lambda k=key: self.sort_by(k))
            self.tree.column(key, width=width, minwidth=40, stretch=(key == "function"),
                             anchor="e" if key in ("qty", "heater_v", "heater_a", "pa_max") else "w")
        vs = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(mid, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        self.tree.bind("<Double-1>", lambda e: self.do_open_sheet())
        self.tree.tag_configure("inferred", foreground="#8a6d00")
        self.tree.tag_configure("equiv", foreground="#0a5a8a")
        panes.add(mid, weight=3)

        # detail
        right = ttk.Frame(panes, width=310)
        sheetbar = ttk.Frame(right)
        sheetbar.pack(fill="x", pady=(0, PAD))
        ttk.Button(sheetbar, text="Open datasheet", command=self.do_open_sheet).pack(side="right")
        ttk.Button(sheetbar, text="RadioMuseum",
                  command=lambda: self.do_lookup("radiomuseum.org")).pack(side="right", padx=(0, 6))
        ttk.Button(sheetbar, text="Web search",
                  command=lambda: self.do_lookup()).pack(side="right", padx=(0, 6))
        self.detail_title = ttk.Label(right, text="", font=("TkDefaultFont", 13, "bold"))
        self.detail_title.pack(anchor="w")
        self.detail_sub = ttk.Label(right, text="", foreground="#666")
        self.detail_sub.pack(anchor="w", pady=(0, PAD))

        form = ttk.Frame(right)
        form.pack(fill="x")
        self.field_vars = {}
        for i, (key, label, _kind) in enumerate(TYPE_FIELDS):
            self.build_type_field_row(form, i, key, label, self.field_vars)
        form.columnconfigure(1, weight=1)

        savebar = ttk.Frame(right)
        savebar.pack(fill="x", pady=(PAD, 0))
        ttk.Button(savebar, text="Save", command=lambda: self.save_type(False)).pack(side="left")
        ttk.Button(savebar, text="Save + confirm",
                   command=lambda: self.save_type(True)).pack(side="left", padx=(6, 0))

        ttk.Label(right, text="Notes", foreground="#666").pack(anchor="w", pady=(PAD, 2))
        self.notes = tk.Text(right, height=3, wrap="word", width=32,
                             font=("TkDefaultFont", 9))
        self.notes.pack(fill="x")

        ttk.Label(right, text="Similar types (may substitute, with modification)",
                 foreground="#666").pack(anchor="w", pady=(PAD, 2))
        self.suggest_tree = ttk.Treeview(right, columns=("info",), show="tree headings", height=6)
        self.suggest_tree.heading("#0", text="Type")
        self.suggest_tree.heading("info", text="Why")
        self.suggest_tree.column("#0", width=64, stretch=False)
        self.suggest_tree.column("info", width=230)
        self.suggest_tree.pack(fill="both", expand=True, pady=(0, 4))
        self.suggest_tree.bind("<Double-1>", lambda e: self.on_suggest_pick())
        self.suggest_tree.tag_configure("heater_diff", foreground="#8a3d00")
        panes.add(right, weight=1)

        # ---- status bar ----
        self.status = ttk.Label(root, text="", anchor="w", foreground="#444")
        self.status.pack(fill="x", pady=(PAD, 0))

    def _build_bases_tab(self, root):
        """Build the Bases/Sockets tab: Add/Take/Move/Delete lot buttons, a
        base/box search bar, and the socket-stock treeview."""
        bar = ttk.Frame(root)
        bar.pack(fill="x", pady=(0, PAD))
        ttk.Button(bar, text="Add", command=self.do_sock_add).pack(side="left")
        ttk.Button(bar, text="Take", command=self.do_sock_take).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Move", command=self.do_sock_move).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Delete lot", command=self.do_sock_delete).pack(side="left", padx=(6, 0))

        filt = ttk.LabelFrame(root, text="Search", padding=PAD)
        filt.pack(fill="x", pady=(0, PAD))
        self.sv_base = tk.StringVar()
        self.sv_box = tk.StringVar()
        specs = [("Base", self.sv_base, 18), ("Box", self.sv_box, 10)]
        for i, (label, var, w) in enumerate(specs):
            ttk.Label(filt, text=label).grid(row=0, column=i * 2, sticky="e", padx=(0 if i == 0 else PAD, 4))
            e = ttk.Entry(filt, textvariable=var, width=w)
            e.grid(row=0, column=i * 2 + 1, sticky="w")
            e.bind("<Return>", lambda ev: self.run_sock_search())
        btns = ttk.Frame(filt)
        btns.grid(row=0, column=4, padx=(PAD * 2, 0))
        ttk.Button(btns, text="Search", command=self.run_sock_search).pack(side="left")
        ttk.Button(btns, text="Clear", command=self.clear_sock_filters).pack(side="left", padx=(6, 0))

        mid = ttk.Frame(root)
        mid.pack(fill="both", expand=True)
        self.sock_tree = ttk.Treeview(mid, columns=[c[0] for c in SOCKET_COLS],
                                      show="headings", selectmode="browse", height=16)
        for key, label, width in SOCKET_COLS:
            self.sock_tree.heading(key, text=label, command=lambda k=key: self.sort_sock(k))
            self.sock_tree.column(key, width=width, minwidth=40, stretch=(key == "notes"),
                                  anchor="e" if key == "qty" else "w")
        vs = ttk.Scrollbar(mid, orient="vertical", command=self.sock_tree.yview)
        self.sock_tree.configure(yscrollcommand=vs.set)
        self.sock_tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=1)

        self.sock_status = ttk.Label(root, text="", anchor="w", foreground="#444")
        self.sock_status.pack(fill="x", pady=(PAD, 0))

    def _build_browse_tab(self, root):
        """Build the Browse tab: a name filter, the cascading category/
        numeric-range facet controls (see PB_CAT_FIELDS/PB_NUM_FIELDS), and
        the results treeview covering every held valve type."""
        filt = ttk.LabelFrame(root, text="Filters (cascading - options narrow as you pick)", padding=PAD)
        filt.pack(fill="x", pady=(0, PAD))

        top = ttk.Frame(filt)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Name contains").pack(side="left")
        self.pb_name = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.pb_name, width=20)
        e.pack(side="left", padx=(4, PAD * 2))
        e.bind("<KeyRelease>", lambda ev: self.pb_run_search())
        ttk.Button(top, text="Clear all filters", command=self.pb_clear).pack(side="left")

        grid = ttk.Frame(filt)
        grid.pack(fill="x")
        self.pb_cat_vars = {}
        self.pb_cat_combos = {}
        col = 0
        for field, label in PB_CAT_FIELDS:
            ttk.Label(grid, text=label).grid(row=0, column=col, sticky="e", padx=(0 if col == 0 else PAD, 4), pady=2)
            var = tk.StringVar()
            var.trace_add("write", lambda *_a: self.pb_run_search())
            cb = ttk.Combobox(grid, textvariable=var, width=16, state="readonly")
            cb.grid(row=0, column=col + 1, sticky="w", pady=2)
            self.pb_cat_vars[field] = var
            self.pb_cat_combos[field] = cb
            col += 2

        self.pb_num_op = {}
        self.pb_num_val = {}
        self.pb_num_combos = {}
        for i, (field, label) in enumerate(PB_NUM_FIELDS):
            r, c = 1 + i // 4, (i % 4) * 3
            ttk.Label(grid, text=label).grid(row=r, column=c, sticky="e", padx=(0 if c == 0 else PAD, 4), pady=2)
            opvar = tk.StringVar()
            opvar.trace_add("write", lambda *_a: self.pb_run_search())
            opbox = ttk.Combobox(grid, textvariable=opvar, values=PB_OPS, width=3, state="readonly")
            opbox.grid(row=r, column=c + 1, sticky="w")
            valvar = tk.StringVar()
            valvar.trace_add("write", lambda *_a: self.pb_run_search())
            valbox = ttk.Combobox(grid, textvariable=valvar, width=10, state="readonly")
            valbox.grid(row=r, column=c + 2, sticky="w", padx=(2, 0), pady=2)
            self.pb_num_op[field] = opvar
            self.pb_num_val[field] = valvar
            self.pb_num_combos[field] = valbox

        mid = ttk.Frame(root)
        mid.pack(fill="both", expand=True)
        self.pb_tree = ttk.Treeview(mid, columns=[c[0] for c in BROWSE_COLS],
                                    show="headings", selectmode="browse", height=16)
        for key, label, width in BROWSE_COLS:
            self.pb_tree.heading(key, text=label, command=lambda k=key: self.pb_sort(k))
            self.pb_tree.column(key, width=width, minwidth=40, stretch=(key == "function"),
                                anchor="e" if key in ("heater_v", "heater_a", "va_max", "pa_max",
                                                       "power_out", "freq_max", "qty") else "w")
        vs = ttk.Scrollbar(mid, orient="vertical", command=self.pb_tree.yview)
        self.pb_tree.configure(yscrollcommand=vs.set)
        self.pb_tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=1)
        self.pb_tree.bind("<Double-1>", lambda e: self.pb_show_boxes())
        self.pb_tree.tag_configure("inferred", foreground="#8a6d00")

        self.pb_status = ttk.Label(root, text="", anchor="w", foreground="#444")
        self.pb_status.pack(fill="x", pady=(PAD, 0))
        self.pb_sort_state = {}
        self.pb_rows = []
        self.pb_all = []

    def _build_bench_tab(self, root):
        """Build the Repair Bench tab: designation/circuit-role entry and
        Identify button, then a two-pane layout - a scrollable identity/
        edit form on the left, in-stock matches and substitute suggestions
        on the right."""
        ttk.Label(root, foreground="#555", wraplength=1100, text=
            "Got a valve out of a set you're repairing? Type its designation, find out what it "
            "is, and see what you've already got that could stand in for it.").pack(
            anchor="w", pady=(0, PAD))

        row = ttk.Frame(root)
        row.pack(fill="x", pady=(0, 4))
        ttk.Label(row, text="Type designation").pack(side="left")
        self.rb_name = tk.StringVar()
        e = ttk.Entry(row, textvariable=self.rb_name, width=16)
        e.pack(side="left", padx=(4, PAD * 2))
        e.bind("<Return>", lambda ev: self.rb_lookup())
        ttk.Label(row, text="Found in (circuit stage)").pack(side="left")
        self.rb_role = tk.StringVar()
        rc = ttk.Combobox(row, textvariable=self.rb_role, width=24, values=[
            "", "RF amp", "IF amp", "Frequency changer / mixer", "Audio pre-amp",
            "Audio output", "Rectifier", "Regulator / stabiliser", "Line output",
            "Local oscillator", "Detector",
        ])
        rc.pack(side="left", padx=(4, PAD * 2))
        rc.bind("<Return>", lambda ev: self.rb_lookup())
        ttk.Button(row, text="Identify", command=self.rb_lookup).pack(side="left")

        self.rb_status = ttk.Label(root, text="type a designation and click Identify",
                                   foreground="#444")
        self.rb_status.pack(anchor="w", pady=(0, PAD))

        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True)

        # ---- left: what is it (scrollable - can run taller than the window) ----
        left_container = ttk.Frame(panes, padding=(0, 0, PAD, 0))
        left = self.make_scrollable(left_container)
        idbar = ttk.Frame(left)
        idbar.pack(fill="x")
        ttk.Button(idbar, text="Open datasheet", command=self.rb_open_sheet).pack(side="left")
        ttk.Button(idbar, text="RadioMuseum",
                  command=lambda: self.rb_lookup_web("radiomuseum.org")).pack(side="left", padx=(6, 0))
        ttk.Button(idbar, text="Web search", command=lambda: self.rb_lookup_web()).pack(
            side="left", padx=(6, 0))
        ttk.Button(idbar, text="Copy prompt", command=self.rb_copy_prompt).pack(
            side="left", padx=(6, 0))
        self.rb_create_btn = ttk.Button(idbar, text="Add to database", command=self.rb_create)
        self.rb_create_btn.pack(side="left", padx=(6, 0))
        self.rb_paste_btn = ttk.Button(idbar, text="Paste & apply...", command=self.rb_paste_apply)
        self.rb_paste_btn.pack(side="left", padx=(6, 0))

        dlrow = ttk.Frame(left)
        dlrow.pack(fill="x", pady=(6, 0))
        ttk.Label(dlrow, text="Datasheet URL").pack(side="left")
        self.rb_sheet_url = tk.StringVar()
        self.rb_url_entry = ttk.Entry(dlrow, textvariable=self.rb_sheet_url)
        self.rb_url_entry.pack(side="left", fill="x", expand=True, padx=(4, 6))
        self.rb_download_btn = ttk.Button(dlrow, text="Download PDF",
                                          command=self.rb_download_sheet)
        self.rb_download_btn.pack(side="left")

        form = ttk.Frame(left)
        form.pack(fill="x", pady=(PAD, 0))
        self.rb_field_vars = {}
        self.rb_field_widgets = {}
        for i, (key, label, _kind) in enumerate(TYPE_FIELDS):
            self.build_type_field_row(form, i, key, label, self.rb_field_vars, height=4,
                                      widgets=self.rb_field_widgets)
        form.columnconfigure(1, weight=1)

        savebar = ttk.Frame(left)
        savebar.pack(fill="x", pady=(PAD, 0))
        self.rb_save_btn = ttk.Button(savebar, text="Save", command=lambda: self.rb_save(False))
        self.rb_save_btn.pack(side="left")
        self.rb_save_confirm_btn = ttk.Button(
            savebar, text="Save + confirm", command=lambda: self.rb_save(True))
        self.rb_save_confirm_btn.pack(side="left", padx=(6, 0))

        ttk.Label(left, text="Notes", foreground="#666").pack(anchor="w", pady=(PAD, 2))
        self.rb_notes = tk.Text(left, height=5, wrap="word", font=("TkDefaultFont", 9))
        self.rb_notes.pack(fill="both", expand=True)
        panes.add(left_container, weight=1)

        # Nothing to hand-edit until the record exists - greyed out (and
        # Save/Paste & apply/Download disabled) until "Add to database", so
        # the two-step flow is visible in the form itself, not just the
        # buttons above it.
        self.rb_set_form_enabled(False)

        # ---- right: what you've got ----
        right = ttk.Frame(panes, padding=(PAD, 0, 0, 0))
        ttk.Label(right, text="In stock now (exact type or a listed equivalent)",
                 foreground="#666").pack(anchor="w")
        m1 = ttk.Frame(right)
        m1.pack(fill="both", expand=True, pady=(2, PAD))
        self.rb_match_tree = ttk.Treeview(
            m1, columns=("type", "box", "qty", "maker", "condition", "why"),
            show="headings", height=6)
        for key, label, width in (("type", "Type", 90), ("box", "Box", 50), ("qty", "Qty", 42),
                                  ("maker", "Maker", 90), ("condition", "Condition", 90),
                                  ("why", "Why", 130)):
            self.rb_match_tree.heading(key, text=label)
            self.rb_match_tree.column(key, width=width, anchor="e" if key == "qty" else "w")
        vs1 = ttk.Scrollbar(m1, orient="vertical", command=self.rb_match_tree.yview)
        self.rb_match_tree.configure(yscrollcommand=vs1.set)
        self.rb_match_tree.pack(side="left", fill="both", expand=True)
        vs1.pack(side="left", fill="y")

        ttk.Label(right, text="Possible substitutes in stock (same function, ratings within 50%)",
                 foreground="#666").pack(anchor="w")
        m2 = ttk.Frame(right)
        m2.pack(fill="both", expand=True, pady=(2, 0))
        self.rb_suggest_tree = ttk.Treeview(m2, columns=("info",), show="tree headings", height=8)
        self.rb_suggest_tree.heading("#0", text="Type")
        self.rb_suggest_tree.heading("info", text="Why")
        self.rb_suggest_tree.column("#0", width=110, stretch=False)
        self.rb_suggest_tree.column("info", width=280)
        vs2 = ttk.Scrollbar(m2, orient="vertical", command=self.rb_suggest_tree.yview)
        self.rb_suggest_tree.configure(yscrollcommand=vs2.set)
        self.rb_suggest_tree.pack(side="left", fill="both", expand=True)
        vs2.pack(side="left", fill="y")
        self.rb_suggest_tree.tag_configure("heater_diff", foreground="#8a3d00")
        self.rb_suggest_tree.bind("<Double-1>", lambda e: self.rb_pick_suggestion())
        panes.add(right, weight=1)

    # ---------------------------------------------------------------- data

    def refresh_boxes(self):
        """Reload the per-box type/qty summary from the database and
        repopulate the box list."""
        self.box_rows = [dict(r) for r in self.con.execute(
            "SELECT box, COUNT(DISTINCT type_key) types, SUM(qty) qty FROM stock "
            "GROUP BY box ORDER BY CAST(box AS INTEGER), box")]
        self.populate_boxes()

    def populate_boxes(self):
        """Redraw the box list from self.box_rows, preserving the current
        selection if it still exists."""
        sel = self.boxlist.selection()
        self.boxlist.delete(*self.boxlist.get_children())
        self.boxlist.insert("", "end", iid="__all__", text="All boxes", values=("", ""))
        for r in self.box_rows:
            self.boxlist.insert("", "end", iid=r["box"],
                                text=f"Box {r['box']}", values=(r["types"], r["qty"]))
        if sel and sel[0] in self.boxlist.get_children(""):
            self.boxlist.selection_set(sel[0])

    def sort_boxes(self, key):
        """Toggle ascending/descending sort of the box list by `key` and
        redraw."""
        asc = not self.box_sort_state.get(key, False)
        self.box_sort_state = {key: asc}

        def sk(r):
            """Sort key for a box row: numeric for box number, else raw value."""
            if key == "box":
                try:
                    return (0, int(r["box"]), "")
                except (ValueError, TypeError):
                    return (1, 0, str(r["box"]))
            v = r.get(key)
            return (0, v, "") if v is not None else (1, 0, "")

        self.box_rows.sort(key=sk, reverse=not asc)
        self.populate_boxes()

    def current_box(self):
        """Return the currently selected box id, or None if nothing (or
        "All boxes") is selected."""
        sel = self.boxlist.selection()
        if not sel or sel[0] == "__all__":
            return None
        return sel[0]

    def run_search(self, *_):
        """Run the Valves tab search: build a SQL WHERE clause from the
        quick filter fields, the selected box, and any advanced filters
        (self.adv), then load and display the matching stock rows."""
        where, args = ["1=1"], []
        if self.v_text.get().strip():
            s = f"%{self.v_text.get().strip().lower()}%"
            where.append("(LOWER(t.name) LIKE ? OR LOWER(t.typical_use) LIKE ? "
                         "OR LOWER(t.notes) LIKE ? OR LOWER(t.equivalents) LIKE ? "
                         "OR LOWER(s.notes) LIKE ?)")
            args += [s] * 5
        if self.v_function.get().strip():
            s = f"%{self.v_function.get().strip().lower()}%"
            where.append("(LOWER(t.function) LIKE ? OR LOWER(t.typical_use) LIKE ?)")
            args += [s, s]
        if self.v_base.get().strip():
            where.append("LOWER(t.base) LIKE ?")
            args.append(f"%{self.v_base.get().strip().lower()}%")
        box = self.current_box()
        if box:
            where.append("s.box = ?")
            args.append(box)
        for field, var in (("t.heater_v", self.v_heater), ("t.pa_max", self.v_pa),
                           ("t.freq_max", self.v_freq)):
            expr = var.get().strip()
            if expr:
                parsed = parse_cmp(expr)
                if not parsed:
                    self.set_status(f"cannot read '{expr}' - try 6.3 or >20")
                    return
                op, val = parsed
                where.append(f"{field} {op} ?")
                args.append(val)

        if self.adv.get("maker"):
            where.append("LOWER(s.manufacturer) LIKE ?")
            args.append(f"%{self.adv['maker'].lower()}%")
        if self.adv.get("condition"):
            where.append("LOWER(s.condition) LIKE ?")
            args.append(f"%{self.adv['condition'].lower()}%")
        if self.adv.get("family"):
            where.append("LOWER(t.family) LIKE ?")
            args.append(f"%{self.adv['family'].lower()}%")
        if self.adv.get("equivalents"):
            where.append("LOWER(t.equivalents) LIKE ?")
            args.append(f"%{self.adv['equivalents'].lower()}%")
        for field, key in (("t.heater_a", "heater_a"), ("t.va_max", "va_max"),
                           ("t.gm", "gm"), ("t.mu", "mu"), ("t.power_out", "power_out")):
            expr = self.adv.get(key)
            if expr:
                parsed = parse_cmp(expr)
                if not parsed:
                    self.set_status(f"cannot read '{expr}' - try 6.3 or >20")
                    return
                op, val = parsed
                where.append(f"{field} {op} ?")
                args.append(val)
        if self.adv.get("confidence"):
            where.append("t.confidence = ?")
            args.append(self.adv["confidence"])
        if self.adv.get("has_sheet") == "yes":
            where.append("t.datasheet_path IS NOT NULL")
        elif self.adv.get("has_sheet") == "no":
            where.append("t.datasheet_path IS NULL")

        sql = f"""SELECT s.id, s.box, COALESCE(t.name, s.type_key) AS type,
                         s.type_key, s.qty, s.manufacturer, s.condition, t.base,
                         t.function, t.heater_v, t.heater_a, t.pa_max,
                         t.datasheet_path, t.confidence
                  FROM stock s LEFT JOIN valve_type t ON s.type_key = t.type_key
                  WHERE {' AND '.join(where)}
                  ORDER BY CAST(s.box AS INTEGER), s.box, type"""
        self.rows = [dict(r) for r in self.con.execute(sql, args)]
        for r in self.rows:
            r["match"] = ""
        self.add_equivalent_rows()
        self.populate()
        self.update_adv_label()

    def add_equivalent_rows(self):
        """If the text search names an exact type, also pull in stock of its
        equivalents (either direction) so a substitute isn't missed just
        because it's filed under a different designation."""
        text = self.v_text.get().strip()
        if not text:
            return
        seed_key = V.norm(text)
        seed = self.con.execute("SELECT type_key, name, equivalents FROM valve_type WHERE type_key=?",
                                (seed_key,)).fetchone()
        if not seed:
            return
        expand = {}  # type_key -> label describing why it's included
        for tok in (seed["equivalents"] or "").split():
            k = V.norm(tok)
            if k and k != seed_key:
                expand[k] = seed["name"]
        for row in self.con.execute("SELECT type_key, name, equivalents FROM valve_type WHERE equivalents IS NOT NULL"):
            if row["type_key"] == seed_key:
                continue
            if any(V.norm(tok) == seed_key for tok in (row["equivalents"] or "").split()):
                expand[row["type_key"]] = row["name"]
        if not expand:
            return
        have_ids = {r["id"] for r in self.rows}
        qmarks = ",".join("?" * len(expand))
        sql = f"""SELECT s.id, s.box, COALESCE(t.name, s.type_key) AS type,
                         s.type_key, s.qty, s.manufacturer, s.condition, t.base,
                         t.function, t.heater_v, t.heater_a, t.pa_max,
                         t.datasheet_path, t.confidence
                  FROM stock s LEFT JOIN valve_type t ON s.type_key = t.type_key
                  WHERE s.type_key IN ({qmarks})
                  ORDER BY CAST(s.box AS INTEGER), s.box, type"""
        for r in self.con.execute(sql, list(expand.keys())):
            r = dict(r)
            if r["id"] in have_ids:
                continue
            r["match"] = f"≈ equiv of {expand[r['type_key']]}"
            self.rows.append(r)

    def update_adv_label(self):
        """Update the "Advanced..." button's label with a count of active
        quick + advanced filters."""
        n = len(self.adv) + sum(1 for v in (self.v_text, self.v_function, self.v_base,
                                            self.v_heater, self.v_pa, self.v_freq)
                                if v.get().strip())
        self.adv_btn.config(text=f"Advanced ({n})" if n else "Advanced...")

    def populate(self):
        """Redraw the Valves tab results tree from self.rows, tagging
        inferred/unconfirmed and equivalent-match rows, and update the
        status line with the row/qty totals."""
        self.tree.delete(*self.tree.get_children())
        for r in self.rows:
            vals = []
            for key, _l, _w in STOCK_COLS:
                if key == "sheet":
                    vals.append("yes" if r["datasheet_path"] else "")
                else:
                    v = r.get(key)
                    vals.append("" if v is None else v)
            tags = []
            if r.get("match"):
                tags.append("equiv")
            elif r["confidence"] == "inferred":
                tags.append("inferred")
            self.tree.insert("", "end", iid=str(r["id"]), values=vals, tags=tuple(tags))
        total = sum(r["qty"] for r in self.rows)
        note = "   -   amber = unconfirmed params"
        if any(r.get("match") for r in self.rows):
            note += ", blue = equivalent of your search"
        self.set_status(f"{len(self.rows)} lots, {total} valves{note}")
        kids = self.tree.get_children()
        if kids:
            self.tree.selection_set(kids[0])
            self.tree.see(kids[0])

    def sort_by(self, key):
        """Toggle ascending/descending sort of the results table by `key`
        and redraw."""
        asc = not self.sort_state.get(key, False)
        self.sort_state = {key: asc}

        def sk(r):
            """Sort key for a result row: numeric for box/numeric columns,
            case-insensitive string otherwise."""
            v = r.get("sheet") if key == "sheet" else r.get(key)
            if key == "box":
                try:
                    return (0, int(r["box"]), "")
                except (ValueError, TypeError):
                    return (1, 0, str(r["box"]))
            if v is None:
                return (1, 0, "")
            if isinstance(v, (int, float)):
                return (0, v, "")
            return (0, 0, str(v).lower())

        self.rows.sort(key=sk, reverse=not asc)
        self.populate()

    def on_box_select(self, _e):
        """Box list selection changed - rerun the search filtered to it."""
        self.run_search()

    def do_advanced_search(self):
        """Open the Advanced search dialog seeded with current quick and
        advanced filter values, then apply whatever the user submits back
        into the quick fields / self.adv and rerun the search."""
        quick = {"text": self.v_text, "function": self.v_function, "base": self.v_base,
                 "heater_v": self.v_heater, "pa_max": self.v_pa, "freq_max": self.v_freq}
        fields = [(key, label, quick[key].get() if key in quick else self.adv.get(key, ""), kind)
                  for key, label, kind in ADV_FIELDS]
        d = FormDialog(self.master, "Advanced search - all fields", fields, ok_label="Apply")
        if d.result is None:
            return
        for key, var in quick.items():
            var.set(d.result.get(key) or "")
        self.adv = {k: v for k, v in d.result.items()
                    if v is not None and k not in ADV_QUICK_KEYS}
        self.run_search()

    def selected_row(self):
        """Return the currently selected row dict from self.rows, or None
        if nothing is selected."""
        sel = self.tree.selection()
        if not sel:
            return None
        return next((r for r in self.rows if str(r["id"]) == sel[0]), None)

    def on_row_select(self, _e):
        """Results tree selection changed - load the detail panel for the
        selected row's type."""
        r = self.selected_row()
        if not r:
            return
        self.load_type(r["type_key"])

    def load_type(self, key):
        """Load `key`'s reference record into the detail panel (title,
        held-qty/box summary, TYPE_FIELDS form, notes) and refresh its
        similar-type suggestions."""
        t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?", (key,)).fetchone()
        self.current_type = key
        if not t:
            self.detail_title.config(text=key)
            self.detail_sub.config(text="no reference record")
            return
        held = self.con.execute("SELECT COALESCE(SUM(qty),0) c FROM stock WHERE type_key=?",
                                (key,)).fetchone()["c"]
        boxes = [str(x["box"]) for x in self.con.execute(
            "SELECT DISTINCT box FROM stock WHERE type_key=? ORDER BY CAST(box AS INTEGER)", (key,))]
        self.detail_title.config(text=t["name"])
        self.detail_sub.config(
            text=f"{held} held in box {', '.join(boxes)}   ·   {t['confidence']}"
                 + (f"   ·   {t['family']}" if t["family"] else ""))
        for k, _l, _kind in TYPE_FIELDS:
            set_field_value(self.field_vars[k], t[k])
        self.notes.delete("1.0", "end")
        self.notes.insert("1.0", t["notes"] or "")
        self.populate_suggestions(t)

    def find_similar(self, ref, limit=8):
        """Other held types with the same broad function and every shared
        electrical parameter within SIMILAR_TOLERANCE - candidates for a
        substitute-with-modification, not a drop-in equivalent."""
        ref_group = function_group(ref["function"])
        if not ref_group:
            return []
        equiv_keys = {V.norm(x) for x in (ref["equivalents"] or "").split()}
        out = []
        for row in self.con.execute("SELECT * FROM valve_type WHERE type_key != ?", (ref["type_key"],)):
            if row["type_key"] in equiv_keys or function_group(row["function"]) != ref_group:
                continue
            deltas, ok = [], True
            for f in SIMILAR_FIELDS:
                rv, cv = ref[f], row[f]
                if rv is None or cv is None or rv == 0:
                    continue
                pct = abs(cv - rv) / rv
                if pct > SIMILAR_TOLERANCE:
                    ok = False
                    break
                deltas.append((f, pct))
            if not ok or not deltas:
                continue
            heater_diff = (ref["heater_v"] is not None and row["heater_v"] is not None
                           and abs(ref["heater_v"] - row["heater_v"]) > 0.3)
            avg_pct = sum(p for _f, p in deltas) / len(deltas)
            out.append((avg_pct, row, deltas, heater_diff))
        out.sort(key=lambda x: x[0])
        return out[:limit]

    def populate_suggestions(self, ref):
        """Refresh the "similar types" tree for `ref` using find_similar(),
        flagging heater-voltage mismatches."""
        self.suggest_tree.delete(*self.suggest_tree.get_children())
        self._suggestions = {}
        for _avg, row, deltas, heater_diff in self.find_similar(ref):
            bits = [f"{f.replace('_max','')} {row[f]:g} ({p*100:.0f}% off)" for f, p in deltas[:2]]
            info = ", ".join(bits)
            if heater_diff:
                info += f"  [heater {row['heater_v']}V vs {ref['heater_v']}V]"
            iid = row["type_key"]
            self._suggestions[iid] = row["type_key"]
            self.suggest_tree.insert("", "end", iid=iid, text=row["name"], values=(info,),
                                     tags=("heater_diff",) if heater_diff else ())

    def on_suggest_pick(self):
        """Load the type selected in the similar-types tree into the
        detail panel."""
        sel = self.suggest_tree.selection()
        if sel:
            self.load_type(sel[0])

    def make_scrollable(self, parent):
        """A vertically-scrolling frame - for the Repair Bench identity pane,
        which is tall enough (datasheet controls + 13-field form + notes) to
        overflow the window on smaller screens with no way to reach what's
        cut off, since a plain packed Frame doesn't scroll on its own."""
        canvas = tk.Canvas(parent, highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        inner = ttk.Frame(canvas)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        def wheel(e):
            """Mouse-wheel handler: scroll the canvas one step per notch."""
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return inner

    def build_type_field_row(self, parent, row, key, label, field_vars, height=3, widgets=None):
        """One row of a TYPE_FIELDS form, used by both the Valves tab detail
        panel and the Repair Bench tab. See MULTILINE_FIELDS. field_vars gets
        the thing you read/write (StringVar or Text - see get/set_field_value);
        widgets, if given, gets the actual widget, for callers that need to
        toggle enabled/disabled state (field_vars alone can't do that for a
        StringVar, since the Entry it's attached to is never otherwise kept)."""
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="nw" if key in MULTILINE_FIELDS else "w", pady=1)
        if key in MULTILINE_FIELDS:
            cell = ttk.Frame(parent)
            cell.grid(row=row, column=1, sticky="ew", pady=1)
            txt = tk.Text(cell, height=height, wrap="word", width=26, font=("TkDefaultFont", 9))
            sb = ttk.Scrollbar(cell, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.pack(side="left", fill="y")
            field_vars[key] = txt
            if widgets is not None:
                widgets[key] = txt
        else:
            var = tk.StringVar()
            field_vars[key] = var
            entry = ttk.Entry(parent, textvariable=var, width=26)
            entry.grid(row=row, column=1, sticky="ew", pady=1)
            if widgets is not None:
                widgets[key] = entry

    def apply_type_fields(self, key, field_vars, notes_widget, confirm):
        """Write a TYPE_FIELDS-shaped form (+ notes) back to valve_type. Shared
        by the Valves tab detail panel and the Repair Bench tab, which each
        have their own widget instances but the same field layout."""
        sets, args = [], []
        for fkey, label, kind in TYPE_FIELDS:
            s = get_field_value(field_vars[fkey])
            if not s:
                sets.append(f"{fkey}=NULL")
                continue
            if kind in (int, float):
                try:
                    val = kind(s)
                except ValueError:
                    messagebox.showerror("Invalid value", f"{label} must be a number")
                    return False
            else:
                val = s
            sets.append(f"{fkey}=?")
            args.append(val)
        sets.append("notes=?")
        args.append(notes_widget.get("1.0", "end").strip() or None)
        if confirm:
            sets.append("confidence='confirmed'")
        args.append(key)
        self.con.execute(f"UPDATE valve_type SET {','.join(sets)} WHERE type_key=?", args)
        self.con.commit()
        return True

    def save_type(self, confirm):
        """Write the Valves tab detail form back to the current type via
        apply_type_fields, then refresh the search results and reload the
        detail panel."""
        if not self.current_type:
            return
        if not self.apply_type_fields(self.current_type, self.field_vars, self.notes, confirm):
            return
        self.set_status(f"saved {self.current_type}"
                        + (" and marked confirmed" if confirm else ""))
        self.run_search()
        self.load_type(self.current_type)

    # ---------------------------------------------------------------- actions

    def do_add(self):
        """Prompt for a new stock lot (type/box/qty/maker/condition/notes)
        and insert it, creating a bare inferred valve_type record first if
        the type isn't already known."""
        boxes = [str(r["box"]) for r in self.con.execute(
            "SELECT DISTINCT box FROM stock ORDER BY CAST(box AS INTEGER)")]
        d = FormDialog(self.master, "Add stock", [
            ("type", "Type", "", str),
            ("box", "Box", self.current_box() or "", boxes),
            ("qty", "Quantity", 1, int),
            ("maker", "Manufacturer", "", str),
            ("condition", "Condition", "",
             ["NOS", "used", "untested", "matched pair", "matched quad"]),
            ("notes", "Notes", "", str),
        ], ok_label="Add")
        if not d.result or not d.result["type"] or not d.result["box"]:
            return
        r = d.result
        key = V.norm(r["type"])
        created = False
        if not self.con.execute("SELECT 1 FROM valve_type WHERE type_key=?", (key,)).fetchone():
            inf = V.classify(r["type"])
            self.con.execute(
                """INSERT INTO valve_type (type_key,name,function,family,heater_v,
                   heater_a,confidence) VALUES (?,?,?,?,?,?,'inferred')""",
                (key, r["type"].strip().upper(), inf.get("function"), inf.get("family"),
                 inf.get("heater_v"), inf.get("heater_a")))
            created = True
        self.con.execute(
            """INSERT INTO stock (type_key,box,qty,manufacturer,condition,date_added,notes)
               VALUES (?,?,?,?,?,?,?)""",
            (key, r["box"], r["qty"] or 1, r["maker"], r["condition"],
             datetime.date.today().isoformat(), r["notes"]))
        self.con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                         (r["box"], "attic"))
        self.con.commit()
        self.refresh_boxes()
        self.run_search()
        self.set_status(f"added {r['qty']} x {r['type']} to box {r['box']}"
                        + ("  (new type created)" if created else ""))

    def do_take(self):
        """Prompt for a quantity to remove from the selected lot; deletes
        the lot outright if the amount taken meets or exceeds what's held."""
        r = self.selected_row()
        if not r:
            self.set_status("select a lot first")
            return
        d = FormDialog(self.master, f"Take {r['type']} from box {r['box']}",
                       [("qty", f"How many (have {r['qty']})", 1, int)], ok_label="Take")
        if not d.result:
            return
        n = d.result["qty"] or 0
        if n <= 0:
            return
        if n >= r["qty"]:
            self.con.execute("DELETE FROM stock WHERE id=?", (r["id"],))
        else:
            self.con.execute("UPDATE stock SET qty=qty-? WHERE id=?", (n, r["id"]))
        self.con.commit()
        self.refresh_boxes()
        self.run_search()
        self.set_status(f"took {min(n, r['qty'])} x {r['type']} from box {r['box']}")

    def do_move(self):
        """Prompt for a destination box and move the selected lot there,
        creating the box record if it doesn't exist yet."""
        r = self.selected_row()
        if not r:
            self.set_status("select a lot first")
            return
        boxes = [str(x["box"]) for x in self.con.execute(
            "SELECT DISTINCT box FROM stock ORDER BY CAST(box AS INTEGER)")]
        d = FormDialog(self.master, f"Move {r['type']}",
                       [("to", "To box", "", boxes)], ok_label="Move")
        if not d.result or not d.result["to"]:
            return
        self.con.execute("UPDATE stock SET box=? WHERE id=?", (d.result["to"], r["id"]))
        self.con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                         (d.result["to"], "attic"))
        self.con.commit()
        self.refresh_boxes()
        self.run_search()
        self.set_status(f"moved {r['type']} to box {d.result['to']}")

    def do_delete(self):
        """Confirm and delete the selected lot entirely."""
        r = self.selected_row()
        if not r:
            return
        if not messagebox.askyesno("Delete lot",
                                   f"Remove all {r['qty']} x {r['type']} from box {r['box']}?"):
            return
        self.con.execute("DELETE FROM stock WHERE id=?", (r["id"],))
        self.con.commit()
        self.refresh_boxes()
        self.run_search()

    def do_open_sheet(self, row=None):
        """Open the datasheet for `row` (or the current selection): a
        locally downloaded copy if one exists, else an online lookup URL
        as a fallback."""
        r = row if row is not None else self.selected_row()
        if not r:
            self.set_status("select a row first")
            return
        path = None
        if r["datasheet_path"]:
            candidate = os.path.join(self.archive, r["datasheet_path"])
            if os.path.exists(candidate):
                path = candidate
        if path:
            try:
                if sys.platform == "darwin":
                    subprocess.run(["open", path], check=False)
                elif os.name == "nt":
                    os.startfile(path)  # noqa
                else:
                    subprocess.run(["xdg-open", path], check=False)
                self.set_status(f"opened {r['datasheet_path']}")
            except Exception as e:
                self.set_status(f"could not open: {e}")
            return
        # No local copy yet - fall back to an online source rather than
        # doing nothing, so the button is always useful. The lookup site
        # wants the bare designation (e.g. 6E6PG), not the punctuated
        # display name (6E6-PG), which it 500s on.
        t = self.con.execute("SELECT datasheet_url FROM valve_type WHERE type_key=?",
                             (r["type_key"],)).fetchone()
        url = (t["datasheet_url"] if t and t["datasheet_url"] else None) or \
              f"https://tdsl.duncanamps.com/show.php?des={urllib.parse.quote(r['type_key'])}"
        webbrowser.open(url)
        self.set_status(f"no local datasheet for {r['type']} - opened {url}")

    def do_lookup(self, site=None, row=None):
        """Open a web search for `row` (or the current selection),
        optionally scoped to `site` (e.g. radiomuseum.org)."""
        r = row if row is not None else self.selected_row()
        if not r:
            self.set_status("select a row first")
            return
        # Site-scoped web search rather than a guessed deep link - RadioMuseum's
        # own URL scheme isn't reliable to construct directly, but a search
        # engine will resolve to the right page (or nothing, if it's not there).
        q = r["type_key"] + " valve tube" + (f" site:{site}" if site else " datasheet")
        url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
        webbrowser.open(url)
        self.set_status(f"opened {'RadioMuseum' if site else 'web'} search for {r['type']}")

    # ---------------------------------------------------------------- repair bench

    def rb_resolve(self, name):
        """Best-effort single type_key match for a typed-in designation -
        exact, then substring, then a listed equivalent. Mirrors valves.py's
        resolve(), simplified to one best guess for this one-at-a-time tool."""
        key = V.norm(name)
        if not key:
            return None
        r = self.con.execute("SELECT type_key FROM valve_type WHERE type_key=?", (key,)).fetchone()
        if r:
            return r["type_key"]
        r = self.con.execute(
            "SELECT type_key FROM valve_type WHERE type_key LIKE ? "
            "ORDER BY LENGTH(type_key) LIMIT 1", (f"%{key}%",)).fetchone()
        if r:
            return r["type_key"]
        r = self.con.execute(
            "SELECT type_key FROM valve_type WHERE UPPER(REPLACE(equivalents,' ','')) LIKE ?",
            (f"%{key}%",)).fetchone()
        return r["type_key"] if r else None

    def rb_lookup(self, *_a):
        """Handle the Repair Bench "Identify" action: resolve the typed
        designation to a type_key, load whatever's known (or an inferred
        guess) into the form, find in-stock matches/substitutes, and
        report status."""
        name = self.rb_name.get().strip()
        if not name:
            self.rb_status.config(text="type a designation first")
            return
        key = self.rb_resolve(name) or V.norm(name)
        if not key:
            self.rb_status.config(text="that doesn't look like a valid designation")
            return
        self.rb_current_key = key
        t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?", (key,)).fetchone()
        self.rb_load_form(t, name, role=self.rb_role.get().strip())
        self.rb_find_matches(key, t)
        if t:
            held = self.con.execute("SELECT COALESCE(SUM(qty),0) c FROM stock WHERE type_key=?",
                                    (key,)).fetchone()["c"]
            self.rb_status.config(
                text=f"{t['name']} - in your database ({t['confidence']}), "
                     + (f"{held} already in stock" if held else "none currently in stock"))
        else:
            self.rb_status.config(
                text=f"'{name}' isn't in your database yet - look it up below, then either "
                     "\"Add to database\" or Save once you've found the real figures")

    def rb_set_form_enabled(self, enabled):
        """Grey out and lock the hand-entry form (fields, notes, Save, Paste
        & apply, datasheet download) until the type actually has a database
        row to write to - editable/white only once it does. Add to database
        is the mirror image: enabled exactly when the rest is disabled."""
        state = "normal" if enabled else "disabled"
        bg = "white" if enabled else "#e8e8e8"
        for widget in self.rb_field_widgets.values():
            widget.config(state=state)
            if isinstance(widget, tk.Text):
                widget.config(background=bg)
        self.rb_notes.config(state=state, background=bg)
        self.rb_save_btn.config(state=state)
        self.rb_save_confirm_btn.config(state=state)
        self.rb_download_btn.config(state=state)
        self.rb_url_entry.config(state=state)
        self.rb_paste_btn.config(state=state)
        self.rb_create_btn.config(state="disabled" if enabled else "normal")

    def rb_load_form(self, t, typed_name, role=""):
        """Fill the Repair Bench form from an existing valve_type row `t`,
        or from a best-effort classification of `typed_name` if there
        isn't one yet; seeds the notes with the circuit `role` when
        starting fresh with no existing notes. Leaves the form enabled
        only if `t` exists (see rb_set_form_enabled)."""
        # Text widgets refuse insert()/delete() while disabled, so unlock
        # first, fill in the values, then apply whatever the correct final
        # enabled/disabled state actually is.
        self.rb_set_form_enabled(True)
        if t:
            for k, _l, _kind in TYPE_FIELDS:
                set_field_value(self.rb_field_vars[k], t[k])
            # Pre-fill the download box if research already turned up a link -
            # a direct .pdf URL is downloadable as-is; anything else (a
            # RadioMuseum page, say) is still worth having ready to paste over.
            self.rb_sheet_url.set(t["datasheet_url"] or "")
            notes_text = t["notes"] or ""
        else:
            inf = V.classify(typed_name)
            for k, _l, _kind in TYPE_FIELDS:
                set_field_value(self.rb_field_vars[k], inf.get(k))
            self.rb_sheet_url.set("")
            notes_text = ""
        if not notes_text and role:
            notes_text = f"Found in: {role}, {datetime.date.today().isoformat()}\n"
        self.rb_notes.delete("1.0", "end")
        if notes_text:
            self.rb_notes.insert("1.0", notes_text)
        self.rb_set_form_enabled(bool(t))

    def rb_find_matches(self, key, t):
        """Populate the Repair Bench "in stock" and "substitutes" trees for
        `key`/`t`: exact and equivalent-designation stock first, then
        find_similar() candidates that are actually held in some quantity."""
        self.rb_match_tree.delete(*self.rb_match_tree.get_children())
        keys = {key: "exact match"}
        if t and t["equivalents"]:
            for tok in t["equivalents"].split():
                k = V.norm(tok)
                if k and k != key:
                    keys.setdefault(k, f"equivalent of {t['name']}")
        for row in self.con.execute(
                "SELECT type_key, name, equivalents FROM valve_type WHERE equivalents IS NOT NULL"):
            if row["type_key"] == key:
                continue
            if any(V.norm(tok) == key for tok in (row["equivalents"] or "").split()):
                keys.setdefault(row["type_key"], f"equivalent of {row['name']}")
        any_matches = False
        for k, why in keys.items():
            for r in self.con.execute(
                    "SELECT s.box, s.qty, s.manufacturer, s.condition, "
                    "COALESCE(t2.name, s.type_key) AS name FROM stock s "
                    "LEFT JOIN valve_type t2 ON t2.type_key = s.type_key "
                    "WHERE s.type_key=? ORDER BY CAST(s.box AS INTEGER), s.box", (k,)):
                any_matches = True
                self.rb_match_tree.insert("", "end", values=(
                    r["name"], r["box"], r["qty"], r["manufacturer"] or "",
                    r["condition"] or "", why))
        if not any_matches:
            self.rb_match_tree.insert("", "end", values=("", "", "", "", "", "none in stock"))

        self.rb_suggest_tree.delete(*self.rb_suggest_tree.get_children())
        if t and t["function"]:
            for _avg, row, deltas, heater_diff in self.find_similar(dict(t), limit=20):
                held = self.con.execute("SELECT COALESCE(SUM(qty),0) c FROM stock WHERE type_key=?",
                                        (row["type_key"],)).fetchone()["c"]
                if not held:
                    continue
                bits = [f"{f.replace('_max','')} {row[f]:g} ({p*100:.0f}% off)" for f, p in deltas[:2]]
                info = ", ".join(bits)
                if heater_diff:
                    info += f"  [heater {row['heater_v']}V vs {t['heater_v']}V]"
                self.rb_suggest_tree.insert(
                    "", "end", iid=row["type_key"], text=f"{row['name']} ({held} held)",
                    values=(info,), tags=("heater_diff",) if heater_diff else ())

    def rb_pick_suggestion(self):
        """Switch the Repair Bench to the type selected in the substitutes
        tree, as if it had been looked up directly."""
        sel = self.rb_suggest_tree.selection()
        if not sel:
            return
        key = sel[0]
        t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?", (key,)).fetchone()
        if not t:
            return
        self.rb_name.set(t["name"])
        self.rb_current_key = key
        self.rb_load_form(t, t["name"])
        self.rb_find_matches(key, t)
        held = self.con.execute("SELECT COALESCE(SUM(qty),0) c FROM stock WHERE type_key=?",
                                (key,)).fetchone()["c"]
        self.rb_status.config(text=f"{t['name']} - in your database ({t['confidence']}), "
                              f"{held} in stock")

    def rb_ensure_type(self, name):
        """Make sure `name`'s type_key has a valve_type row, creating a bare
        one (classified from the designation, no stock) if this is the first
        time it's been seen. Saving or applying a result for a type you
        haven't explicitly "added" yet should just work - requiring a
        separate create step first is exactly the friction this tab exists
        to remove. Returns (type_key, created) - key is None if `name` is
        empty/unparseable."""
        key = V.norm(name)
        if not key:
            return None, False
        if self.con.execute("SELECT 1 FROM valve_type WHERE type_key=?", (key,)).fetchone():
            return key, False
        inf = V.classify(name)
        self.con.execute(
            """INSERT INTO valve_type (type_key,name,function,family,heater_v,heater_a,confidence)
               VALUES (?,?,?,?,?,?,'inferred')""",
            (key, name.strip(), inf.get("function"), inf.get("family"), inf.get("heater_v"),
             inf.get("heater_a")))
        self.con.commit()
        return key, True

    def rb_create(self):
        """Handle "Add to database": ensure the typed designation has a
        valve_type row (creating a bare inferred one if this is the first
        time it's been seen), then load it into the form."""
        name = self.rb_name.get().strip()
        if not name:
            self.rb_status.config(text="type a designation first")
            return
        key, created = self.rb_ensure_type(name)
        if not key:
            self.rb_status.config(text="that doesn't look like a valid designation")
            return
        self.rb_current_key = key
        t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?", (key,)).fetchone()
        self.rb_load_form(t, name)
        self.rb_find_matches(key, t)
        if created:
            self.rb_status.config(
                text=f"added {name} to your database (reference only, no stock) - "
                     "fill in what you find below, then Save")
        else:
            self.rb_status.config(text=f"{name} is already in your database")

    def rb_save(self, confirm):
        """Write the Repair Bench form back to the current type via
        apply_type_fields, then refresh its match/substitute lists so they
        reflect the just-saved parameters."""
        # The form is greyed out and Save disabled until the type has a
        # database row (see rb_set_form_enabled) - this is a defensive
        # backstop, not the normal path to get here.
        if not self.rb_current_key or not self.con.execute(
                "SELECT 1 FROM valve_type WHERE type_key=?", (self.rb_current_key,)).fetchone():
            self.rb_status.config(text='not in your database yet - click "Add to database" first')
            return
        if not self.apply_type_fields(self.rb_current_key, self.rb_field_vars, self.rb_notes, confirm):
            return
        t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?",
                             (self.rb_current_key,)).fetchone()
        self.rb_find_matches(self.rb_current_key, t)
        self.rb_status.config(
            text=f"saved {t['name']}" + (" and marked confirmed" if confirm else "")
                 + " - substitutes on the right now reflect the saved parameters")

    def rb_open_sheet(self):
        """Open the datasheet for the current Repair Bench type - thin
        wrapper around do_open_sheet using the typed designation."""
        name = self.rb_name.get().strip()
        if not name:
            self.rb_status.config(text="type a designation first")
            return
        key = self.rb_current_key or V.norm(name)
        t = self.con.execute("SELECT datasheet_path FROM valve_type WHERE type_key=?",
                             (key,)).fetchone()
        self.do_open_sheet({"type_key": key, "type": name,
                            "datasheet_path": t["datasheet_path"] if t else None})

    def rb_lookup_web(self, site=None):
        """Open a web search for the current Repair Bench type - thin
        wrapper around do_lookup using the typed designation."""
        name = self.rb_name.get().strip()
        if not name:
            self.rb_status.config(text="type a designation first")
            return
        key = self.rb_current_key or V.norm(name)
        self.do_lookup(site, {"type_key": key, "type": name})

    def rb_copy_prompt(self):
        """Build a research prompt asking an LLM for this type's reference
        electrical parameters (with explicit instructions not to fabricate
        or guess), and copy it to the clipboard for use in a chat."""
        name = self.rb_name.get().strip()
        if not name:
            self.rb_status.config(text="type a designation first")
            return
        role = self.rb_role.get().strip()
        context = f" Pulled from the {role} stage of a set I'm repairing." if role else ""
        lines = [
            "You are researching reference electrical parameters for ONE vacuum-tube (valve) "
            f"type for a personal inventory database: {name}.{context} This data may inform a "
            "real repair, so ACCURACY MATTERS: only record a value if a source clearly and "
            "specifically states it for THIS exact type designation - never estimate, guess, or "
            "borrow figures from a similar-looking type without confirming they're the same "
            "tube. If you can't find reliable data, say so - do not fabricate.", "",
            "Search manufacturer datasheets, radiomuseum.org, Duncan's TDSL "
            "(https://tdsl.duncanamps.com/show.php?des=DESIGNATION), frank.pocnet.net, and "
            "general web search as needed. Find: function, base/socket, pins, heater voltage or "
            "current, max anode voltage, max anode dissipation, gm (mA/V), mu, power output (W), "
            "max frequency (MHz), a short typical-use description in your own words (not copied "
            "verbatim - copyright), any equivalent designations, and a source URL - if you find "
            "a direct link to a PDF datasheet, give THAT as source_url in preference to a "
            "reference page, since I can download it straight from that link.", "",
            "If a field genuinely isn't stated anywhere you can find, leave it blank after the "
            "colon - don't write \"not found\" or similar, and don't put anything there that "
            "isn't the actual value (a number mentioned only in passing, e.g. as part of this "
            "type's own designation, is not a value for that field).", "",
            "Output format - exactly this, nothing else:", "",
            name.upper().strip(), "function:", "base:", "pins:", "heater_v:", "heater_a:",
            "va_max:", "pa_max:", "gm:", "mu:", "power_out:", "freq_max:", "typical_use:",
            "equivalents:", "source_url:", "confidence_note:", "---", "",
            "--- HOW TO USE THE RESULT ---",
            "Copy my whole reply, then back in the app: Repair Bench tab > "
            "\"Paste & apply results...\", paste it in, and Apply.",
        ]
        prompt = "\n".join(lines)
        self.master.clipboard_clear()
        self.master.clipboard_append(prompt)
        self.rb_status.config(text=f"research prompt for {name} copied to clipboard - "
                              "paste it into a Claude chat")

    def rb_paste_apply(self):
        """Open a dialog to paste a research reply (from rb_copy_prompt's
        prompt) and apply whatever fields it confirms to the current type."""
        d = tk.Toplevel(self.master)
        d.title("Paste Claude's reply")
        d.geometry("620x480")
        d.transient(self.master)
        ttk.Label(d, padding=PAD, text=
            "Paste Claude's whole reply below (the block-format research result), then Apply. "
            "Only fields it actually confirmed get written - blanks are left alone.").pack(
            anchor="w")
        body = ttk.Frame(d)
        body.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        txt = tk.Text(body, wrap="word", font=("TkDefaultFont", 9))
        sb = ttk.Scrollbar(body, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        txt.focus_set()

        def apply_it():
            """Parse the pasted text and write any confirmed fields to the
            current type, then refresh the form and match lists."""
            text = txt.get("1.0", "end").strip()
            if not text:
                return
            # The button that opens this dialog is disabled until the type
            # has a database row (see rb_set_form_enabled) - this is a
            # defensive backstop, not the normal path to get here.
            if not self.rb_current_key or not self.con.execute(
                    "SELECT 1 FROM valve_type WHERE type_key=?",
                    (self.rb_current_key,)).fetchone():
                messagebox.showerror("Not in your database yet",
                                     'Click "Add to database" first, then apply the result.')
                return
            try:
                import import_researched as ir
                records = ir.parse_blocks(text)
            except Exception as e:
                messagebox.showerror("Could not read reply", str(e))
                return
            if not records:
                messagebox.showerror(
                    "No data found",
                    "Couldn't find any \"field: value\" lines in the pasted text - make sure "
                    "you copied Claude's whole reply, including the field labels.")
                return
            # This tool already knows which single type the prompt was for -
            # apply the first parsed block straight to it rather than trusting
            # a name match against whatever header line Claude wrote (a stray
            # intro sentence before the data, e.g. "Here's what I found for
            # EM87:", would otherwise be misread as the header and silently
            # produce a record for the wrong key, applying nothing here).
            _hdr, (rec, source, conf_note) = next(iter(records.items()))
            applied, skipped, missing = ir.apply_records(
                self.con, {self.rb_current_key: (rec, source, conf_note)}, dry_run=False)
            self.con.commit()
            d.destroy()
            self.run_search()
            t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?",
                                 (self.rb_current_key,)).fetchone()
            self.rb_load_form(t, t["name"])
            self.rb_find_matches(self.rb_current_key, t)
            if applied:
                self.rb_status.config(text=f"applied research to {t['name']}")
            elif skipped:
                self.rb_status.config(
                    text=f"no usable data in the pasted text for {t['name']} (equivalents-only "
                         "or all fields were hedged/blank)")
            else:
                self.rb_status.config(text="could not apply - check the pasted text format")

        btns = ttk.Frame(d, padding=(PAD, 0, PAD, PAD))
        btns.pack(fill="x")
        ttk.Button(btns, text="Cancel", command=d.destroy).pack(side="right")
        ttk.Button(btns, text="Apply", command=apply_it).pack(side="right", padx=(0, 6))
        d.bind("<Escape>", lambda e: d.destroy())

    def rb_download_sheet(self):
        """Download the URL in the datasheet field, warn if it doesn't
        look like a PDF, and on confirmation save it under the archive
        folder (keyed by type) and record the path on the valve_type row."""
        key = self.rb_current_key
        if not key:
            self.rb_status.config(text="look up or add a type first")
            return
        if not self.con.execute("SELECT 1 FROM valve_type WHERE type_key=?", (key,)).fetchone():
            self.rb_status.config(text='not in your database yet - click "Add to database" first')
            return
        url = self.rb_sheet_url.get().strip()
        if not url:
            self.rb_status.config(text="paste a datasheet URL first")
            return
        import urllib.request
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
        except Exception as e:
            messagebox.showerror("Download failed", str(e))
            return
        is_pdf = data[:4] == b"%PDF"
        warn = "" if is_pdf else "\n\nThis doesn't look like a PDF file - save it anyway?"
        if not messagebox.askyesno(
                "Save datasheet?",
                f"Downloaded {len(data) / 1024:.0f} KB from:\n{url}\n\n"
                f"Save as this collection's datasheet for {key}?{warn}"):
            return
        subdir = key[0] if key[0].isalnum() else "_"
        folder = os.path.join(self.archive, subdir)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{key}.pdf")
        with open(path, "wb") as f:
            f.write(data)
        rel = os.path.relpath(path, self.archive)
        self.con.execute("UPDATE valve_type SET datasheet_path=? WHERE type_key=?", (rel, key))
        self.con.commit()
        t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?", (key,)).fetchone()
        self.rb_load_form(t, t["name"])
        self.rb_find_matches(key, t)
        self.rb_status.config(text=f"saved datasheet for {t['name']} to {rel}")

    # ---------------------------------------------------------------- tools

    def do_scan(self):
        """Tools > Scan datasheet archive. Walks self.archive, indexes every
        .pdf/.png/.gif/.jpg by its normalized filename stem (a '~suffix' after
        the stem is dropped, so e.g. 'EL84~2.pdf' still matches type key EL84),
        and links the file path onto any valve_type row that doesn't already
        have a datasheet_path. Does not overwrite an existing link."""
        if not os.path.isdir(self.archive):
            self.set_status(f"archive folder not found: {self.archive}"
                            f" - Tools > Set archive folder")
            return
        index = {}
        for dirpath, _d, files in os.walk(self.archive):
            for f in files:
                if f.lower().endswith((".pdf", ".png", ".gif", ".jpg")):
                    stem = V.norm(os.path.splitext(f)[0].split("~")[0])
                    if stem:
                        index.setdefault(stem, os.path.relpath(os.path.join(dirpath, f),
                                                               self.archive))
        n = 0
        for r in self.con.execute("SELECT type_key FROM valve_type WHERE datasheet_path IS NULL"):
            p = index.get(r["type_key"])
            if p:
                self.con.execute("UPDATE valve_type SET datasheet_path=? WHERE type_key=?",
                                 (p, r["type_key"]))
                n += 1
        self.con.commit()
        self.run_search()
        self.set_status(f"{len(index)} files in archive, {n} newly linked")

    def do_set_archive(self):
        """Tools > Set archive folder. Lets the user repoint the datasheet
        archive folder for the rest of this session; not persisted to disk,
        so it reverts to the --archive default (or its default) next launch."""
        d = filedialog.askdirectory(title="Datasheet archive folder")
        if d:
            self.archive = d
            self.set_status(f"archive folder: {d}")

    def do_stats(self):
        """Tools > Collection summary. Builds and displays a plain-text report
        of headline counts plus a breakdown of held valves by function and by
        box, in a TextWindow."""
        q = lambda s: self.con.execute(s).fetchone()[0]
        confirmed = self.con.execute(
            "SELECT COUNT(*) FROM valve_type WHERE confidence = ?", ("confirmed",)
        ).fetchone()[0]
        lines = [
            f"types             {q('SELECT COUNT(*) FROM valve_type')}",
            f"stock lots        {q('SELECT COUNT(*) FROM stock')}",
            f"valves total      {q('SELECT SUM(qty) FROM stock')}",
            f"boxes in use      {q('SELECT COUNT(DISTINCT box) FROM stock')}",
            f"datasheets held   {q('SELECT COUNT(*) FROM valve_type WHERE datasheet_path IS NOT NULL')}",
            f"confirmed params  {confirmed}",
            f"bases/sockets     {q('SELECT COALESCE(SUM(qty),0) FROM socket')}",
            "", "by function:",
        ]
        for r in self.con.execute("""
                SELECT COALESCE(t.function,'(unclassified)') fn,
                       COUNT(DISTINCT t.type_key) types, SUM(s.qty) valves
                FROM valve_type t JOIN stock s ON s.type_key=t.type_key
                GROUP BY 1 ORDER BY valves DESC"""):
            lines.append(f"  {r['fn'][:40]:<42}{r['types']:>4} types{r['valves']:>7} valves")
        lines += ["", "by box:"]
        for r in self.con.execute("""SELECT box, COUNT(*) lots, SUM(qty) valves
                                     FROM stock GROUP BY box
                                     ORDER BY valves DESC"""):
            lines.append(f"  box {r['box']:<8}{r['lots']:>4} lots {r['valves']:>5} valves")
        TextWindow(self.master, "Collection summary", "\n".join(lines))

    def do_gaps(self):
        """Tools > What needs data. Lists held types missing a datasheet
        (top 60 by quantity) and held types with no function classified,
        in a TextWindow - a to-do list for research/download prompts."""
        lines = ["Types held with no datasheet linked", "-" * 46]
        for r in self.con.execute("""
                SELECT t.name, SUM(s.qty) qty, COALESCE(t.function,'') fn
                FROM valve_type t JOIN stock s ON s.type_key=t.type_key
                WHERE t.datasheet_path IS NULL
                GROUP BY t.type_key ORDER BY qty DESC LIMIT 60"""):
            lines.append(f"  {r['name']:<14}{r['qty']:>5}   {r['fn'][:34]}")
        lines += ["", "Types with no function classified", "-" * 46]
        for r in self.con.execute("""
                SELECT t.name, SUM(s.qty) qty FROM valve_type t
                JOIN stock s ON s.type_key=t.type_key
                WHERE t.function IS NULL GROUP BY t.type_key ORDER BY qty DESC"""):
            lines.append(f"  {r['name']:<14}{r['qty']:>5}")
        TextWindow(self.master, "What needs data", "\n".join(lines))

    def do_dupes(self):
        """Tools > Possible duplicate types. Flags type_key pairs where one is
        a short prefix of the other (within 2 extra characters, min length 3)
        as candidates for manual review/merge - a cheap heuristic, not proof,
        since e.g. 30FL1 and 30FL14 are genuinely different valves."""
        keys = [r["type_key"] for r in
                self.con.execute("SELECT type_key FROM valve_type ORDER BY type_key")]
        pairs = []
        for i, k in enumerate(keys):
            for k2 in keys[i + 1:]:
                if k2.startswith(k) and len(k2) - len(k) <= 2 and len(k) >= 3:
                    pairs.append((k, k2))
        body = ["Candidate duplicates - review before merging.",
                "Many are genuinely different valves (30FL1 vs 30FL14).",
                "Merge from the command line:  valves.py merge A B --yes", "", ]
        body += [f"  {a:<12} {b}" for a, b in pairs]
        TextWindow(self.master, "Possible duplicate types", "\n".join(body))

    def do_help_guide(self):
        """Help > User guide. Renders a long static walkthrough of the whole
        tool (adding/removing stock, searching, the Repair Bench tab, filling
        in reference data via Claude, datasheets, backups, and export) in a
        proportional-font TextWindow. Keep this in sync by hand if workflow
        changes - it isn't generated from anything."""
        body = "\n".join([
            "VALVE INVENTORY - USER GUIDE", "",
            "Two front ends sharing one database: this window, and valves.py on the command "
            "line. Four tabs here - Valves, Bases / Sockets, Browse, Repair Bench.",
            "",
            "ADDING STOCK", "",
            "  One at a time    \"Add stock\" (Valves tab) / \"Add\" (Bases-Sockets tab). "
            "Creates the type automatically if it's new, classifying it from its designation.",
            "  In bulk          Tools > Import upload CSV..., using the column layout from "
            "Tools > Create upload template... (writes a blank CSV ready to fill in).",
            "  From messy data  Tools > Generate CSV-building prompt... writes a prompt for "
            "any Claude chat. It interviews you (or reads whatever spreadsheet, notes, or "
            "photos you describe) and hands back a ready-to-import CSV.",
            "",
            "REMOVING / MOVING STOCK", "",
            "  Select a row, then Take (use up some of a lot), Move (to another box), or "
            "Delete lot (removes it - asks first). Same from the command line: "
            "valves.py take/move TYPE ...",
            "",
            "SEARCHING & BROWSING", "",
            "  Valves tab search row - text, function, base, and the numeric fields (accept "
            "'>20', '<7', '>=250'). Searching a type also pulls in anything cross-referenced "
            "as its equivalent, shown in blue and labelled which type it's equivalent to. "
            "Advanced... opens every remaining field.",
            "  Browse tab - dropdown filters that cascade (Category, Base, Family, "
            "Confidence, Variable-mu - picking one narrows what the others offer), plus "
            "<, =, > on every numeric rating, and a live name filter as you type. "
            "Double-click a type for its box breakdown, full reference data, and "
            "datasheet/web-search shortcuts.",
            "",
            "REPAIR BENCH TAB", "",
            "  For \"I've got this valve out of a set I'm fixing - what is it, and what have I "
            "got that could stand in for it?\". Type the designation (and optionally which "
            "circuit stage it came from), click Identify.",
            "  If it's already in your database, its reference data loads straight in, \"In "
            "stock now\" shows any you already hold of that exact type or a listed equivalent, "
            "and \"Possible substitutes\" lists other held types with the same broad function "
            "and every shared rating within 50% (heater mismatches are flagged, not hidden - a "
            "dropping resistor often covers that). Double-click a substitute to switch to it.",
            "  If it's new to you: Open datasheet / RadioMuseum / Web search work immediately "
            "off the typed designation, and Copy research prompt puts a ready-to-paste, "
            "single-type version of the research prompt (see below) on the clipboard. Add to "
            "database creates a bare reference record (no stock) so you've somewhere to save "
            "what you find; Save / Save + confirm work exactly as in the Valves tab detail "
            "panel, and refresh the substitute list immediately using the parameters you just "
            "entered.",
            "",
            "FILLING IN REFERENCE DATA", "",
            "  Parameters start out inferred from the type's naming convention, not read from "
            "a datasheet - unconfirmed rows show amber in the Valves tab.",
            "  By hand    Edit the fields in the detail panel, then Save + confirm.",
            "  With Claude:",
            "    Tools > Generate research prompt...             electrical parameters",
            "    Tools > Generate datasheet download prompt...   PDFs into the local archive",
            "  Paste either into Claude - the research prompt works in any chat; the download "
            "one needs an agent with file/web access (Claude Code), since it writes files to "
            "disk. Save the reply to a text file, then Tools > Apply researched data... (or "
            "'import_researched.py <file> --yes' from the command line). Only what Claude "
            "actually confirmed gets applied - a hedged finding ('could not verify', "
            "'plausible') stays flagged as a lead, not marked confirmed.",
            "",
            "DATASHEETS", "",
            "  Double-click a row, or \"Open datasheet\", opens the local PDF if there is one, "
            "otherwise falls back to a web lookup (RadioMuseum / Web search do the same, "
            "scoped to that site). Tools > Scan datasheet archive links newly-added PDF files "
            "in by filename. fetch_datasheets.py builds the archive itself from "
            "frank.pocnet.net (see README) - it's gitignored and not included when you "
            "export, so rebuild it locally or use the download prompt above.",
            "",
            "BACKUP & VERSION CONTROL", "",
            "  valves.db is the live database - gitignored, since it's binary and can't be "
            "diffed. snapshot.py writes data/*.csv and valves.sql, a text snapshot that IS "
            "meant to be committed - that's the real backup and history. After cloning or "
            "restoring elsewhere: 'snapshot.py --restore' rebuilds valves.db from data/.",
            "",
            "EXPORT & GIVING THIS TO SOMEONE ELSE", "",
            "  File > Export spreadsheet...  a plain .xlsx for anyone who just wants to look, "
            "not use the tool.",
            "  File > Export archive and tools (.zip)...  the whole toolkit (code, docs, a "
            "fresh data/ snapshot) zipped up, with an option to strip the third-party "
            "descriptive notes text first. See QUICKSTART.md, included in the zip:",
            "    1. Unzip, run 'python3 snapshot.py --restore', then 'python3 valves_gui.py'.",
            "    2. Datasheets aren't included - rebuild with fetch_datasheets.py, or Tools > "
            "Generate datasheet download prompt... with Claude.",
            "    3. Add their own stock the same ways described above.",
            "",
            "Everything here also works from the command line - see README.md for the full "
            "command reference.",
        ])
        TextWindow(self.master, "User guide", body, wrap="word", proportional=True)

    def do_about(self):
        """Help > About. Static version/summary dialog box."""
        messagebox.showinfo(
            "About",
            "Valve inventory\n\n"
            "A SQLite database and desktop/CLI tool for cataloguing a vacuum-tube collection - "
            "1,441 valves, 253 types, 36 boxes and counting.\n\n"
            "See README.md for the full picture, or Help > User guide for a task-by-task "
            "walkthrough.")

    def do_open_manual(self, filename):
        """Help menu handler for one of the three PDF manuals shipped in
        docs/. Opens filename with the OS default PDF viewer (os.startfile on
        Windows, 'open' on macOS, 'xdg-open' elsewhere); if the PDF is
        missing, points the user at docs/build_manuals.py to regenerate it
        rather than failing silently."""
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "docs", filename)
        if not os.path.exists(path):
            messagebox.showerror(
                "Manual not found",
                f"{filename} isn't in docs/. Regenerate it with:\n"
                "  python3 docs/build_manuals.py\n(requires: pip install reportlab)")
            return
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            elif os.name == "nt":
                os.startfile(path)  # noqa
            else:
                subprocess.run(["xdg-open", path], check=False)
            self.set_status(f"opened {filename}")
        except Exception as e:
            self.set_status(f"could not open: {e}")

    def do_export(self):
        """File > Export spreadsheet. Prompts for a save path and delegates to
        the CLI's cmd_export (valves.py) to write a plain .xlsx snapshot of
        the whole inventory, for someone who just wants to look at the data
        without running the tool."""
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", initialfile="valve_inventory.xlsx",
            filetypes=[("Excel workbook", "*.xlsx")])
        if not path:
            return
        try:
            import valves as cli
            ns = argparse.Namespace(path=path)
            cli.cmd_export(self.con, ns)
            self.set_status(f"exported to {path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def do_open_db(self):
        """File > Open database. Switches the whole app to a different .db
        file: closes the current connection, opens the new one via
        V.init_db, updates the window title, and refreshes every tab's
        data (boxes, valve search, socket search)."""
        path = filedialog.askopenfilename(filetypes=[("SQLite database", "*.db"), ("All", "*")])
        if not path:
            return
        self.con.close()
        self.dbpath = path
        self.con = V.init_db(path)
        self.master.title(f"Valve inventory - {os.path.basename(path)}")
        self.refresh_boxes()
        self.run_search()
        self.run_sock_search()

    def do_export_archive(self):
        """File > Export archive and tools (.zip). Bundles the code, docs,
        and a freshly-regenerated data/ snapshot into a zip for handing the
        whole toolkit to someone else. Offers to strip the typical_use/notes
        text first, since that descriptive text was originally sourced from
        r-type.org and isn't the user's to redistribute freely (see README);
        stripping it leaves classifications, parameters, and box locations
        untouched. Datasheets themselves are never included (gitignored,
        not the user's to redistribute either)."""
        import zipfile
        path = filedialog.asksaveasfilename(
            defaultextension=".zip", initialfile="valve_inventory_export.zip",
            filetypes=[("Zip archive", "*.zip")])
        if not path:
            return
        strip = messagebox.askyesno(
            "Strip descriptive notes?",
            "The typical_use/notes fields carry some descriptive text originally gathered from "
            "r-type.org, which isn't yours to republish freely (see README).\n\n"
            "Strip it from this export? (Classifications, parameters and box locations are "
            "unaffected either way.)")
        here = os.path.dirname(os.path.abspath(__file__))
        try:
            import snapshot as snap
            snap.snapshot(argparse.Namespace(db=self.dbpath, strip_notes=strip))
        except Exception as e:
            messagebox.showerror("Export failed", f"could not refresh the snapshot: {e}")
            return
        include = ["valves.py", "valves_gui.py", "valvelib.py", "snapshot.py",
                  "fetch_datasheets.py", "build_db.py", "test_smoke.py",
                  "import_researched.py", "upload_template.csv", "run.bat",
                  "README.md", "QUICKSTART.md", "LICENSE"]
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fn in include:
                    fp = os.path.join(here, fn)
                    if os.path.exists(fp):
                        zf.write(fp, arcname=fn)
                data_dir = os.path.join(here, "data")
                for fn in sorted(os.listdir(data_dir)):
                    if fn.endswith((".csv", ".sql")):
                        zf.write(os.path.join(data_dir, fn), arcname=f"data/{fn}")
                docs_dir = os.path.join(here, "docs")
                if os.path.isdir(docs_dir):
                    for fn in sorted(os.listdir(docs_dir)):
                        if fn.endswith((".pdf", ".py")):
                            zf.write(os.path.join(docs_dir, fn), arcname=f"docs/{fn}")
            self.set_status(f"exported archive + tools to {path}")
            messagebox.showinfo(
                "Export complete",
                f"Written to:\n{path}\n\nRecipient unzips it, then runs:\n"
                "  python3 snapshot.py --restore\n  python3 valves_gui.py\n\n"
                "(full walkthrough in QUICKSTART.md, included in the zip)")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def do_import_csv(self):
        """Tools > Import upload CSV. Prompts for a CSV (see
        upload_template.csv for the expected columns) and delegates to the
        CLI's cmd_import_csv, then refreshes the box list and search
        results. New types are classified automatically from their
        designation; existing types just gain stock."""
        path = filedialog.askopenfilename(
            title="Upload CSV (see upload_template.csv for the columns)",
            filetypes=[("CSV file", "*.csv"), ("All", "*")])
        if not path:
            return
        try:
            import valves as cli
            cli.cmd_import_csv(self.con, argparse.Namespace(file=path))
            self.refresh_boxes()
            self.run_search()
            self.set_status(f"imported stock from {path}")
        except Exception as e:
            messagebox.showerror("Import failed", str(e))

    def do_create_upload_template(self):
        """Tools > Create upload template. Writes a blank CSV with just the
        header row (type,box,qty,maker,condition,notes) for the user to fill
        in before Tools > Import upload CSV."""
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="upload_template.csv",
            filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("type,box,qty,maker,condition,notes\n")
        self.set_status(f"wrote a blank upload template to {path}")
        messagebox.showinfo(
            "Template written",
            f"Wrote a blank upload template to:\n{path}\n\n"
            "One row per lot - type and box are required, the rest optional. Fill it in, then "
            "Tools > Import upload CSV...")

    def do_generate_csv_prompt(self):
        """Tools > Generate CSV-building prompt. Writes a static, self-
        contained prompt (no live DB data needed) instructing Claude to
        interview the user about messy/incomplete records and hand back a
        CSV using the same header as do_create_upload_template's template,
        ready for Tools > Import upload CSV. Works in any plain chat - no
        file/web access required, unlike the research/download prompts."""
        lines = [
            "You are helping me turn my own valve/tube collection records into a CSV file for "
            "the valve-inventory tool. I have some existing data - it might be a spreadsheet, "
            "photos of boxes, handwritten notes, or just me telling you what I remember - and "
            "it's probably inconsistent or incomplete.", "",
            "Please interview me to fill in the gaps rather than guessing: ask me, one box or "
            "batch at a time, for the type designation, which box/location it's in, how many, "
            "and (optional) the manufacturer, condition, and any notes. If I give you a rough "
            "photo description or a messy list, parse what you can and ask about anything "
            "unclear or ambiguous rather than assuming.", "",
            "Once we've gone through everything, write it out as a CSV with this exact header "
            "and column order:", "",
            "type,box,qty,maker,condition,notes", "",
            "One row per lot. type and box are required for every row; use 1 for qty if not "
            "given, and leave maker/condition/notes blank rather than guessing. Give me the "
            "finished CSV as a code block I can save directly to a file.", "",
            "--- HOW TO USE THE RESULT ---",
            "Save my reply as a .csv file, then run:",
            "  python3 valves.py import-csv <file>.csv",
            "or use Tools > Import upload CSV... in the GUI. New types get classified "
            "automatically from their designation; existing types just get more stock added.",
        ]
        prompt = "\n".join(lines)
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="csv_builder_prompt.txt",
            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt)
        self.set_status(f"wrote a CSV-building prompt to {path}")
        messagebox.showinfo(
            "Prompt written",
            f"Wrote a CSV-building prompt to:\n{path}\n\n"
            "Paste it into any Claude chat (no file/web access needed for this one), answer "
            "its questions, save the CSV it gives you, then Tools > Import upload CSV...")

    def do_generate_prompt(self):
        """Tools > Generate research prompt. Picks the top 60 held types
        (by quantity) that are unconfirmed, unclassified, or missing a
        datasheet, and writes a prompt asking Claude to research their
        electrical parameters. The output block format (TYPE_NAME followed
        by 'field:' lines and a '---' separator) exactly matches what
        import_researched.py's parse_blocks() expects, including the
        confidence_note field it scans for hedging language - that's what
        lets a saved reply be applied straight back with Tools > Apply
        researched data... (or import_researched.py <file> --yes)."""
        rows = [dict(r) for r in self.con.execute("""
            SELECT t.type_key, t.name, COALESCE(SUM(s.qty),0) qty, t.function
            FROM valve_type t LEFT JOIN stock s ON s.type_key=t.type_key
            WHERE t.confidence='inferred' OR t.function IS NULL OR t.datasheet_path IS NULL
            GROUP BY t.type_key ORDER BY qty DESC LIMIT 60""")]
        if not rows:
            messagebox.showinfo("Nothing to research", "Every held type is already confirmed.")
            return
        lines = [
            "You are researching reference electrical parameters for vacuum-tube (valve) types "
            "for a personal inventory database. This data may inform real amplifier builds, so "
            "ACCURACY MATTERS: only record a value if a source clearly and specifically states "
            "it for THIS exact type designation. Never estimate, guess, or borrow figures from "
            "a similar-looking type without confirming they're the same tube. If you can't find "
            "reliable data, say so - do not fabricate.", "",
            "Search manufacturer datasheets, radiomuseum.org, Duncan's TDSL "
            "(https://tdsl.duncanamps.com/show.php?des=DESIGNATION), frank.pocnet.net, and "
            "general web search as needed.", "",
            "For each type below, find: function, base/socket, pins, heater voltage or current, "
            "max anode voltage, max anode dissipation, gm (mA/V), mu, power output (W), max "
            "frequency (MHz), a short typical-use description IN YOUR OWN WORDS (not copied "
            "verbatim - copyright), any equivalent designations, and the source URL.", "",
            "Types to research (name, held quantity):",
        ]
        for r in rows:
            lines.append(f"{r['name']}\tqty={r['qty']}"
                        + ("" if not r["function"] else f"\t(current guess: {r['function']})"))
        lines += [
            "", "Output format: for EACH type, one block exactly like this (leave a field "
            "blank after the colon if you couldn't confirm it - don't write 'unknown', just "
            "leave it blank):", "",
            "TYPE_NAME", "function:", "base:", "pins:", "heater_v:", "heater_a:", "va_max:",
            "pa_max:", "gm:", "mu:", "power_out:", "freq_max:", "typical_use:", "equivalents:",
            "source_url:",
            "confidence_note: (e.g. 'multiple sources agree', or 'could not verify, low "
            "confidence')", "---", "",
            "Respond with ONLY these blocks, one per type, nothing else - no preamble, no "
            "summary.", "",
            "--- HOW TO USE THE RESULTS ---",
            "Save my reply to a text file, then run:",
            "  python3 import_researched.py <file> --yes",
            "or use Tools > Apply researched data... in the GUI.",
        ]
        prompt = "\n".join(lines)
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="research_prompt.txt",
            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt)
        self.set_status(f"wrote research prompt for {len(rows)} types to {path}")
        messagebox.showinfo(
            "Prompt written",
            f"Wrote a research prompt for {len(rows)} types to:\n{path}\n\n"
            "Paste its contents into Claude (claude.ai or Claude Code), save the reply to a "
            "text file, then use Tools > Apply researched data...")

    def do_generate_download_prompt(self):
        """Tools > Generate datasheet download prompt. Lists every held type
        still missing a datasheet_path and writes a prompt for an agent with
        file/web access (e.g. Claude Code) to fetch PDFs: run
        fetch_datasheets.py first for cheap bulk coverage, then search
        per-type for whatever's left, saving each PDF under
        datasheets/<first letter>/<type key>.pdf so Tools > Scan datasheet
        archive can link it in by filename. Unlike do_generate_prompt, this
        one won't work in a plain chat session since it writes files to
        disk."""
        rows = [dict(r) for r in self.con.execute("""
            SELECT t.type_key, t.name, COALESCE(SUM(s.qty),0) qty
            FROM valve_type t LEFT JOIN stock s ON s.type_key=t.type_key
            WHERE t.datasheet_path IS NULL
            GROUP BY t.type_key ORDER BY qty DESC""")]
        if not rows:
            messagebox.showinfo("Nothing to fetch", "Every held type already has a linked datasheet.")
            return
        lines = [
            "You are building a local datasheet archive for a personal vacuum-tube (valve) "
            "inventory tool (valves.py / valves_gui.py). This needs an agent with file-system "
            "AND web access (e.g. Claude Code) - it won't work in a plain chat session, since "
            "it has to actually write files to disk.", "",
            "First, try the tool's own fetcher, which cheaply covers most European/British "
            "types from a single hobbyist archive:",
            "  python3 fetch_datasheets.py --index      # skip if url_index.json already exists",
            "  python3 fetch_datasheets.py --download",
            "  python3 valves.py scan",
            "That's rate-limited (2s/request, please don't lower it) and resumable - let it "
            "finish before moving on. It only pulls from frank.pocnet.net, so it will miss "
            "transmitting/military/Russian types that site doesn't carry.", "",
            "Then, for whatever's STILL missing a datasheet after that (recheck with "
            "`python3 valves.py gaps`), search per type: manufacturer archives (Eimac/CPI for "
            "transmitting tubes, Duncan's TDSL at "
            "https://tdsl.duncanamps.com/show.php?des=DESIGNATION, which is good for "
            "higher-power tubes), radiomuseum.org, and df6na.de for Russian/Soviet "
            "designations. Only use a source you're confident is genuinely for this exact "
            "type - a wrong-but-plausible match is worse than no datasheet at all (this has "
            "happened before in this collection: an auto-downloaded 'R71.pdf' turned out to "
            "be an unrelated phototube, not the rectifier this actually is).", "",
            "If a WebFetch-style tool garbles a PDF's binary content, that doesn't mean the "
            "PDF is bad - fetch/save the raw file and read it directly instead.", "",
            "When you find a genuine PDF datasheet:",
            "  1. Save it to  datasheets/<first letter of the type key>/<type key>.pdf",
            "     e.g. EL84 -> datasheets/E/EL84.pdf, 6146B -> datasheets/6/6146B.pdf",
            "     (the type key is the name with punctuation stripped, e.g. ECF80 not "
            "ECF80/CV5215 - check with `python3 valves.py show TYPE` if unsure)",
            "  2. Run  python3 valves.py scan  to link it in, or if the filename won't match "
            "automatically, set it directly:",
            "       python3 valves.py set TYPE --datasheet-path <path relative to datasheets/>",
            "If you find a good page but can't get a PDF (HTML-only, or blocked), record the "
            "URL instead so there's still a lead:",
            "     python3 valves.py set TYPE --datasheet-url <url>", "",
            "Types still missing a datasheet (name, held quantity):",
        ]
        for r in rows:
            lines.append(f"{r['name']}\tqty={r['qty']}")
        lines += [
            "", "When you're done, run  python3 snapshot.py  to refresh the committed data/ "
            "snapshot with whatever got linked (the datasheets themselves aren't committed - "
            "see README - only the fact that a type now has one).",
        ]
        prompt = "\n".join(lines)
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="datasheet_download_prompt.txt",
            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt)
        self.set_status(f"wrote datasheet-download prompt for {len(rows)} types to {path}")
        messagebox.showinfo(
            "Prompt written",
            f"Wrote a datasheet-download prompt for {len(rows)} types to:\n{path}\n\n"
            "This one needs an agent with file/web access (Claude Code, not a plain chat) "
            "since it downloads files to disk. Paste it in and let it run, then reopen this "
            "database (or Tools > Scan datasheet archive) to pick up whatever it found.")

    def do_apply_research(self):
        """Tools > Apply researched data. Loads a saved Claude reply (the text
        produced from do_generate_prompt's output), parses it into blocks via
        import_researched.apply_records, and writes confirmed fields into the
        database - the GUI equivalent of
        'import_researched.py <file> --yes'. Reports which types were
        applied, skipped (block present but no usable data), or not found in
        the database."""
        path = filedialog.askopenfilename(
            title="Researched data (Claude's reply, saved as text)",
            filetypes=[("Text file", "*.txt"), ("All", "*")])
        if not path:
            return
        try:
            import import_researched as ir
            with open(path, encoding="utf-8") as f:
                records = ir.parse_blocks(f.read())
            applied, skipped, missing = ir.apply_records(self.con, records, dry_run=False)
        except Exception as e:
            messagebox.showerror("Apply failed", str(e))
            return
        self.con.commit()
        self.run_search()
        msg = f"Applied {len(applied)} types."
        if skipped:
            msg += f"\nSkipped (no data found): {', '.join(skipped)}"
        if missing:
            msg += f"\nNot in database: {', '.join(missing)}"
        self.set_status(f"applied research data from {path}: {len(applied)} types")
        messagebox.showinfo("Applied", msg)

    def clear_filters(self):
        """Resets every Valves-tab search field (text, function, base,
        heater, power, frequency, and the advanced-filter dict) and the box
        list back to 'all', then reruns the search."""
        for v in (self.v_text, self.v_function, self.v_base,
                  self.v_heater, self.v_pa, self.v_freq):
            v.set("")
        self.adv = {}
        self.boxlist.selection_set("__all__")
        self.run_search()

    def set_status(self, msg):
        """Writes msg to the status bar at the foot of the main window."""
        self.status.config(text=msg)

    # ---------------------------------------------------------------- bases/sockets

    def run_sock_search(self, *_):
        """Bases/Sockets tab: rebuilds self.sock_rows from the socket table
        using the base (substring) and box (exact, case-insensitive) filter
        fields, then repopulates the tree. Bound to those fields' traces, so
        it also fires as the user types; *_ absorbs the Tk trace callback
        args."""
        where, args = ["1=1"], []
        if self.sv_base.get().strip():
            where.append("LOWER(base) LIKE ?")
            args.append(f"%{self.sv_base.get().strip().lower()}%")
        if self.sv_box.get().strip():
            where.append("box = ? COLLATE NOCASE")
            args.append(self.sv_box.get().strip())
        sql = f"""SELECT id, box, base, qty, condition, notes FROM socket
                  WHERE {' AND '.join(where)} ORDER BY base, CAST(box AS INTEGER), box"""
        self.sock_rows = [dict(r) for r in self.con.execute(sql, args)]
        self.populate_sock()

    def populate_sock(self):
        """Redraws the Bases/Sockets tree from self.sock_rows (already
        filtered/sorted by the caller) and updates the lot/total-count status
        line."""
        self.sock_tree.delete(*self.sock_tree.get_children())
        for r in self.sock_rows:
            vals = ["" if r.get(k) is None else r.get(k) for k, _l, _w in SOCKET_COLS]
            self.sock_tree.insert("", "end", iid=str(r["id"]), values=vals)
        total = sum(r["qty"] for r in self.sock_rows)
        self.sock_status.config(text=f"{len(self.sock_rows)} lots, {total} bases/sockets")

    def sort_sock(self, key):
        """Bases/Sockets column-header click handler: toggles ascending/
        descending for key (clicking a different column always starts
        ascending, since sock_sort_state is replaced rather than merged) and
        re-sorts self.sock_rows in place."""
        asc = not self.sock_sort_state.get(key, False)
        self.sock_sort_state = {key: asc}

        def sk(r):
            """Sort key: box sorts numerically where possible (so box 9 <
            box 10), falling back to string sort for non-numeric box labels;
            None values always sort last regardless of direction."""
            v = r.get(key)
            if key == "box":
                try:
                    return (0, int(r["box"]), "")
                except (ValueError, TypeError):
                    return (1, 0, str(r["box"]))
            if v is None:
                return (1, 0, "")
            if isinstance(v, (int, float)):
                return (0, v, "")
            return (0, 0, str(v).lower())

        self.sock_rows.sort(key=sk, reverse=not asc)
        self.populate_sock()

    def selected_sock(self):
        """Returns the socket-table dict row matching the currently selected
        tree item, or None if nothing is selected."""
        sel = self.sock_tree.selection()
        if not sel:
            return None
        return next((r for r in self.sock_rows if str(r["id"]) == sel[0]), None)

    def clear_sock_filters(self):
        """Clears the Bases/Sockets base and box filter fields and reruns the
        search."""
        self.sv_base.set("")
        self.sv_box.set("")
        self.run_sock_search()

    def do_sock_add(self):
        """Bases/Sockets 'Add': prompts for base type, box, quantity,
        condition, and notes via FormDialog, inserts a new socket lot, and
        creates the box (default location 'attic') if it doesn't already
        exist."""
        boxes = [str(r["box"]) for r in self.con.execute(
            "SELECT DISTINCT box FROM stock ORDER BY CAST(box AS INTEGER)")]
        d = FormDialog(self.master, "Add base/socket stock", [
            ("base", "Base (e.g. B9A, Octal)", "", str),
            ("box", "Box", self.sv_box.get() or "", boxes),
            ("qty", "Quantity", 1, int),
            ("condition", "Condition", "", ["NOS", "used", "untested"]),
            ("notes", "Notes", "", str),
        ], ok_label="Add")
        if not d.result or not d.result["base"] or not d.result["box"]:
            return
        r = d.result
        self.con.execute("INSERT INTO socket (base,box,qty,condition,notes) VALUES (?,?,?,?,?)",
                         (r["base"].strip(), r["box"], r["qty"] or 1, r["condition"], r["notes"]))
        self.con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                         (r["box"], "attic"))
        self.con.commit()
        self.run_sock_search()
        self.sock_status.config(text=f"added {r['qty']} x {r['base']} to box {r['box']}")

    def do_sock_take(self):
        """Bases/Sockets 'Take': prompts for a quantity to remove from the
        selected lot. Deletes the row outright if the amount taken meets or
        exceeds what's held, otherwise decrements qty in place."""
        r = self.selected_sock()
        if not r:
            self.sock_status.config(text="select a lot first")
            return
        d = FormDialog(self.master, f"Take {r['base']} from box {r['box']}",
                       [("qty", f"How many (have {r['qty']})", 1, int)], ok_label="Take")
        if not d.result:
            return
        n = d.result["qty"] or 0
        if n <= 0:
            return
        if n >= r["qty"]:
            self.con.execute("DELETE FROM socket WHERE id=?", (r["id"],))
        else:
            self.con.execute("UPDATE socket SET qty=qty-? WHERE id=?", (n, r["id"]))
        self.con.commit()
        self.run_sock_search()
        self.sock_status.config(text=f"took {min(n, r['qty'])} x {r['base']} from box {r['box']}")

    def do_sock_move(self):
        """Bases/Sockets 'Move': prompts for a destination box and moves the
        selected lot there, creating the destination box row if needed."""
        r = self.selected_sock()
        if not r:
            self.sock_status.config(text="select a lot first")
            return
        boxes = [str(x["box"]) for x in self.con.execute(
            "SELECT DISTINCT box FROM stock ORDER BY CAST(box AS INTEGER)")]
        d = FormDialog(self.master, f"Move {r['base']}",
                       [("to", "To box", "", boxes)], ok_label="Move")
        if not d.result or not d.result["to"]:
            return
        self.con.execute("UPDATE socket SET box=? WHERE id=?", (d.result["to"], r["id"]))
        self.con.execute("INSERT OR IGNORE INTO box (box, location) VALUES (?,?)",
                         (d.result["to"], "attic"))
        self.con.commit()
        self.run_sock_search()
        self.sock_status.config(text=f"moved {r['base']} to box {d.result['to']}")

    def do_sock_delete(self):
        """Bases/Sockets 'Delete lot': confirms, then deletes the whole
        selected lot."""
        r = self.selected_sock()
        if not r:
            return
        if not messagebox.askyesno("Delete lot",
                                   f"Remove all {r['qty']} x {r['base']} from box {r['box']}?"):
            return
        self.con.execute("DELETE FROM socket WHERE id=?", (r["id"],))
        self.con.commit()
        self.run_sock_search()

    # ---------------------------------------------------------------- parametric browser

    def pb_load_all(self):
        """category/variable_mu aren't real columns, so filtering happens in
        Python over the whole (small, ~250-row) type list rather than SQL."""
        rows = [dict(r) for r in self.con.execute("""
            SELECT t.*, COALESCE(SUM(s.qty),0) qty
            FROM valve_type t LEFT JOIN stock s ON s.type_key = t.type_key
            GROUP BY t.type_key""")]
        for r in rows:
            r["category"] = browse_category(r.get("function"))
            r["variable_mu"] = "yes" if is_variable_mu(r) else "no"
        return rows

    def pb_matches(self, r, exclude=None):
        """Returns True if type row r satisfies every active Browse-tab
        filter (name substring, category dropdowns, numeric comparisons).
        exclude skips one field's own filter when checking whether r would
        still match the OTHER active filters - used by pb_refresh_dropdowns
        to compute each dropdown's options as if its own current selection
        weren't applied, so cascading filters narrow each other without a
        field hiding its own possible values."""
        name = self.pb_name.get().strip().lower()
        if name and name not in (r.get("name") or "").lower():
            return False
        for field, _label in PB_CAT_FIELDS:
            if field == exclude:
                continue
            val = self.pb_cat_vars[field].get()
            if val and str(r.get(field) or "") != val:
                return False
        for field, _label in PB_NUM_FIELDS:
            if field == exclude:
                continue
            op = self.pb_num_op[field].get()
            val = self.pb_num_val[field].get()
            if op and val:
                try:
                    fval = float(val)
                except ValueError:
                    continue
                rv = r.get(field)
                if rv is None or not compare_op(rv, op, fval):
                    return False
        return True

    def pb_refresh_dropdowns(self):
        """Recompute each Browse-tab dropdown's option list from what the
        *other* active filters still allow (see pb_matches' `exclude`), so
        the facets cascade like a shopping-site filter panel."""
        for field, _label in PB_CAT_FIELDS:
            subset = [r for r in self.pb_all if self.pb_matches(r, exclude=field)]
            vals = sorted({str(r[field]) for r in subset if r.get(field)})
            self.pb_cat_combos[field]["values"] = [""] + vals
        for field, _label in PB_NUM_FIELDS:
            subset = [r for r in self.pb_all if self.pb_matches(r, exclude=field)]
            vals = sorted({r[field] for r in subset if r.get(field) is not None})
            self.pb_num_combos[field]["values"] = [
                f"{v:g}" if isinstance(v, float) else str(v) for v in vals]

    def pb_run_search(self, *_a):
        """Reload every type, apply the current Browse-tab filters, and refresh
        the results table and the cascading dropdown option lists."""
        self.pb_all = self.pb_load_all()
        self.pb_rows = [r for r in self.pb_all if self.pb_matches(r)]
        self.pb_rows.sort(key=lambda r: r["name"])
        self.pb_populate()
        self.pb_refresh_dropdowns()

    def pb_populate(self):
        """Redraw the Browse tab's results tree from self.pb_rows."""
        self.pb_tree.delete(*self.pb_tree.get_children())
        for r in self.pb_rows:
            vals = ["" if r.get(k) is None else r.get(k) for k, _l, _w in BROWSE_COLS]
            tag = "inferred" if r.get("confidence") == "inferred" else ""
            self.pb_tree.insert("", "end", iid=r["type_key"], values=vals, tags=(tag,))
        total_qty = sum(r["qty"] for r in self.pb_rows)
        self.pb_status.config(
            text=f"{len(self.pb_rows)} types, {total_qty} valves"
                 f"   -   double-click a row for its box breakdown")

    def pb_sort(self, key):
        """Sort the Browse tab's results by `key`, toggling direction on repeat clicks."""
        asc = not self.pb_sort_state.get(key, False)
        self.pb_sort_state = {key: asc}

        def sk(r):
            """Sort key: blanks last, numbers before case-insensitive strings."""
            v = r.get(key)
            if v is None:
                return (1, 0, "")
            if isinstance(v, (int, float)):
                return (0, v, "")
            return (0, 0, str(v).lower())

        self.pb_rows.sort(key=sk, reverse=not asc)
        self.pb_populate()

    def pb_clear(self):
        """Reset every Browse-tab filter and rerun the search."""
        self.pb_name.set("")
        for field, _label in PB_CAT_FIELDS:
            self.pb_cat_vars[field].set("")
        for field, _label in PB_NUM_FIELDS:
            self.pb_num_op[field].set("")
            self.pb_num_val[field].set("")
        self.pb_run_search()

    def pb_show_boxes(self):
        """Open a TypeDetailWindow for the selected Browse-tab row (double-click handler)."""
        sel = self.pb_tree.selection()
        if not sel:
            return
        key = sel[0]
        t = self.con.execute("SELECT * FROM valve_type WHERE type_key=?", (key,)).fetchone()
        if not t:
            return
        rows = [dict(r) for r in self.con.execute(
            "SELECT box, qty, manufacturer, condition FROM stock WHERE type_key=? "
            "ORDER BY CAST(box AS INTEGER), box", (key,))]
        TypeDetailWindow(self, dict(t), rows)


def main():
    """CLI entry point: parse --db/--archive, offer to restore a fresh
    database from data/valves.sql if this looks like a brand-new clone or
    export, then build the Tk root window and App and run the event loop."""
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=V.DB_DEFAULT)
    p.add_argument("--archive", default=V.ARCHIVE_DEFAULT)
    a = p.parse_args()

    root = tk.Tk()
    root.withdraw()  # stay hidden until setup below is done, to avoid a flash of an empty window

    # First run from a fresh clone or export: valves.db doesn't exist yet,
    # but there's a data/valves.sql snapshot sitting right there to build it
    # from. V.init_db() below would happily open a brand-new, silently EMPTY
    # database instead - the single biggest point of confusion for anyone who
    # skips the documented restore step (see README/QUICKSTART.md). Offer to
    # do it now rather than let that happen with no explanation.
    here = os.path.dirname(os.path.abspath(__file__))
    sql_dump = os.path.join(here, "data", "valves.sql")
    if not os.path.exists(a.db) and os.path.exists(sql_dump):
        if messagebox.askyesno(
                "Set up the database",
                f"{os.path.basename(a.db)} doesn't exist yet, but this folder has a "
                "data/valves.sql snapshot to build it from.\n\n"
                "Restore the database from that snapshot now?"):
            import snapshot as snap
            snap.restore(argparse.Namespace(db=a.db, force=False))

    try:
        style = ttk.Style()
        for theme in ("clam", "vista", "aqua", "default"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        style.configure("Treeview", rowheight=22)
        style.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))
    except tk.TclError:
        pass
    App(root, a.db, a.archive)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
