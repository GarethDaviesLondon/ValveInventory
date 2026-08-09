#!/usr/bin/env python3
"""
valves_gui.py - desktop front end for the valve inventory.

Same database and same library as valves.py; this is only a different way in.
Run with:  python3 valves_gui.py [--db valves.db] [--archive datasheets]
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

PAD = 8

STOCK_COLS = [
    ("box", "Box", 50), ("type", "Type", 100), ("qty", "Qty", 42),
    ("manufacturer", "Maker", 88), ("condition", "Condition", 92),
    ("function", "Function", 190), ("heater_v", "Htr V", 48),
    ("heater_a", "Htr A", 48), ("pa_max", "Pa W", 46), ("sheet", "Sheet", 44),
]

TYPE_FIELDS = [
    ("function", "Function", str), ("base", "Base", str), ("pins", "Pins", int),
    ("heater_v", "Heater V", float), ("heater_a", "Heater A", float),
    ("va_max", "Va max V", float), ("pa_max", "Pa max W", float),
    ("gm", "gm mA/V", float), ("mu", "mu", float),
    ("power_out", "Power out W", float), ("freq_max", "Freq max MHz", float),
    ("equivalents", "Equivalents", str), ("typical_use", "Typical use", str),
]


def parse_cmp(expr):
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
    def __init__(self, parent, title, body):
        super().__init__(parent)
        self.title(title)
        self.geometry("640x540")
        self.transient(parent)
        txt = tk.Text(self, wrap="none", font="TkFixedFont",
                      borderwidth=0, padx=PAD, pady=PAD)
        sb = ttk.Scrollbar(self, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        txt.insert("1.0", body)
        txt.configure(state="disabled")
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx() + 90}+{parent.winfo_rooty() + 60}")


# --------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------

class App(ttk.Frame):
    def __init__(self, master, db, archive):
        super().__init__(master, padding=PAD)
        self.master = master
        self.dbpath = db
        self.archive = archive
        self.con = V.init_db(db)
        self.current_type = None
        self.sort_state = {}

        master.title(f"Valve inventory - {os.path.basename(db)}")
        master.geometry("1280x780")
        master.minsize(1000, 620)
        self.pack(fill="both", expand=True)

        self._build_menu()
        self._build_layout()
        self.refresh_boxes()
        self.run_search()

    # ---------------------------------------------------------------- chrome

    def _build_menu(self):
        m = tk.Menu(self.master)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label="Export spreadsheet...", command=self.do_export)
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
        m.add_cascade(label="Tools", menu=t)
        self.master.config(menu=m)

    def _build_layout(self):
        # ---- toolbar ----
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, PAD))
        ttk.Button(bar, text="Add stock", command=self.do_add).pack(side="left")
        ttk.Button(bar, text="Take", command=self.do_take).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Move", command=self.do_move).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Delete lot", command=self.do_delete).pack(side="left", padx=(6, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=PAD)
        ttk.Button(bar, text="Open datasheet", command=self.do_open_sheet).pack(side="left")

        # ---- filter row ----
        filt = ttk.LabelFrame(self, text="Search", padding=PAD)
        filt.pack(fill="x", pady=(0, PAD))

        self.v_text = tk.StringVar()
        self.v_function = tk.StringVar()
        self.v_maker = tk.StringVar()
        self.v_heater = tk.StringVar()
        self.v_pa = tk.StringVar()
        self.v_freq = tk.StringVar()

        specs = [("Text", self.v_text, 20), ("Function", self.v_function, 18),
                 ("Maker", self.v_maker, 12), ("Heater V", self.v_heater, 8),
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

        # ---- three panes ----
        panes = ttk.PanedWindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)

        # boxes sidebar
        left = ttk.Frame(panes)
        ttk.Label(left, text="Boxes").pack(anchor="w")
        self.boxlist = ttk.Treeview(left, columns=("lots", "qty"), height=12)
        self.boxlist.heading("#0", text="Box")
        self.boxlist.heading("lots", text="Lots")
        self.boxlist.heading("qty", text="Valves")
        self.boxlist.column("#0", width=90)
        self.boxlist.column("lots", width=48, anchor="e")
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
        self.tree.tag_configure("inferred", foreground="#8a6d00")
        panes.add(mid, weight=3)

        # detail
        right = ttk.Frame(panes, width=310)
        self.detail_title = ttk.Label(right, text="", font=("TkDefaultFont", 13, "bold"))
        self.detail_title.pack(anchor="w")
        self.detail_sub = ttk.Label(right, text="", foreground="#666")
        self.detail_sub.pack(anchor="w", pady=(0, PAD))

        form = ttk.Frame(right)
        form.pack(fill="x")
        self.field_vars = {}
        for i, (key, label, _kind) in enumerate(TYPE_FIELDS):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=1)
            var = tk.StringVar()
            self.field_vars[key] = var
            ttk.Entry(form, textvariable=var, width=26).grid(row=i, column=1, sticky="ew", pady=1)
        form.columnconfigure(1, weight=1)

        savebar = ttk.Frame(right)
        savebar.pack(fill="x", pady=(PAD, 0))
        ttk.Button(savebar, text="Save", command=lambda: self.save_type(False)).pack(side="left")
        ttk.Button(savebar, text="Save + confirm",
                   command=lambda: self.save_type(True)).pack(side="left", padx=(6, 0))

        ttk.Label(right, text="Notes", foreground="#666").pack(anchor="w", pady=(PAD, 2))
        self.notes = tk.Text(right, height=5, wrap="word", width=32,
                             font=("TkDefaultFont", 9))
        self.notes.pack(fill="both", expand=True)
        panes.add(right, weight=1)

        # ---- status bar ----
        self.status = ttk.Label(self, text="", anchor="w", foreground="#444")
        self.status.pack(fill="x", pady=(PAD, 0))

    # ---------------------------------------------------------------- data

    def refresh_boxes(self):
        self.boxlist.delete(*self.boxlist.get_children())
        self.boxlist.insert("", "end", iid="__all__", text="All boxes", values=("", ""))
        rows = self.con.execute(
            "SELECT box, COUNT(*) lots, SUM(qty) qty FROM stock GROUP BY box "
            "ORDER BY CAST(box AS INTEGER), box")
        for r in rows:
            self.boxlist.insert("", "end", iid=r["box"],
                                text=f"Box {r['box']}", values=(r["lots"], r["qty"]))

    def current_box(self):
        sel = self.boxlist.selection()
        if not sel or sel[0] == "__all__":
            return None
        return sel[0]

    def run_search(self, *_):
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
        if self.v_maker.get().strip():
            where.append("LOWER(s.manufacturer) LIKE ?")
            args.append(f"%{self.v_maker.get().strip().lower()}%")
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

        sql = f"""SELECT s.id, s.box, COALESCE(t.name, s.type_key) AS type,
                         s.type_key, s.qty, s.manufacturer, s.condition,
                         t.function, t.heater_v, t.heater_a, t.pa_max,
                         t.datasheet_path, t.confidence
                  FROM stock s LEFT JOIN valve_type t ON s.type_key = t.type_key
                  WHERE {' AND '.join(where)}
                  ORDER BY CAST(s.box AS INTEGER), s.box, type"""
        self.rows = [dict(r) for r in self.con.execute(sql, args)]
        self.populate()

    def populate(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.rows:
            vals = []
            for key, _l, _w in STOCK_COLS:
                if key == "sheet":
                    vals.append("yes" if r["datasheet_path"] else "")
                else:
                    v = r.get(key)
                    vals.append("" if v is None else v)
            tag = "inferred" if r["confidence"] == "inferred" else ""
            self.tree.insert("", "end", iid=str(r["id"]), values=vals, tags=(tag,))
        total = sum(r["qty"] for r in self.rows)
        self.set_status(f"{len(self.rows)} lots, {total} valves"
                        f"   -   amber rows have unconfirmed parameters")
        kids = self.tree.get_children()
        if kids:
            self.tree.selection_set(kids[0])
            self.tree.see(kids[0])

    def sort_by(self, key):
        asc = not self.sort_state.get(key, False)
        self.sort_state = {key: asc}

        def sk(r):
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
        self.run_search()

    def selected_row(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return next((r for r in self.rows if str(r["id"]) == sel[0]), None)

    def on_row_select(self, _e):
        r = self.selected_row()
        if not r:
            return
        self.load_type(r["type_key"])

    def load_type(self, key):
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
            v = t[k]
            self.field_vars[k].set("" if v is None else str(v))
        self.notes.delete("1.0", "end")
        self.notes.insert("1.0", t["notes"] or "")

    def save_type(self, confirm):
        if not self.current_type:
            return
        sets, args = [], []
        for key, label, kind in TYPE_FIELDS:
            s = self.field_vars[key].get().strip()
            if not s:
                sets.append(f"{key}=NULL")
                continue
            if kind in (int, float):
                try:
                    val = kind(s)
                except ValueError:
                    messagebox.showerror("Invalid value", f"{label} must be a number")
                    return
            else:
                val = s
            sets.append(f"{key}=?")
            args.append(val)
        sets.append("notes=?")
        args.append(self.notes.get("1.0", "end").strip() or None)
        if confirm:
            sets.append("confidence='confirmed'")
        args.append(self.current_type)
        self.con.execute(f"UPDATE valve_type SET {','.join(sets)} WHERE type_key=?", args)
        self.con.commit()
        self.set_status(f"saved {self.current_type}"
                        + (" and marked confirmed" if confirm else ""))
        self.run_search()
        self.load_type(self.current_type)

    # ---------------------------------------------------------------- actions

    def do_add(self):
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

    def do_open_sheet(self):
        r = self.selected_row()
        if not r:
            return
        if not r["datasheet_path"]:
            self.set_status(f"no local datasheet for {r['type']} - "
                            f"run Tools > Scan datasheet archive")
            return
        path = os.path.join(self.archive, r["datasheet_path"])
        if not os.path.exists(path):
            self.set_status(f"file missing: {path}")
            return
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

    # ---------------------------------------------------------------- tools

    def do_scan(self):
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
        d = filedialog.askdirectory(title="Datasheet archive folder")
        if d:
            self.archive = d
            self.set_status(f"archive folder: {d}")

    def do_stats(self):
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

    def do_export(self):
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
        path = filedialog.askopenfilename(filetypes=[("SQLite database", "*.db"), ("All", "*")])
        if not path:
            return
        self.con.close()
        self.dbpath = path
        self.con = V.init_db(path)
        self.master.title(f"Valve inventory - {os.path.basename(path)}")
        self.refresh_boxes()
        self.run_search()

    def clear_filters(self):
        for v in (self.v_text, self.v_function, self.v_maker,
                  self.v_heater, self.v_pa, self.v_freq):
            v.set("")
        self.boxlist.selection_set("__all__")
        self.run_search()

    def set_status(self, msg):
        self.status.config(text=msg)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=V.DB_DEFAULT)
    p.add_argument("--archive", default=V.ARCHIVE_DEFAULT)
    a = p.parse_args()

    root = tk.Tk()
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
    root.mainloop()


if __name__ == "__main__":
    main()
