#!/usr/bin/env python3
"""
i18n.py - run the desktop app in English or Portuguese.

Hernani Capela catalogued this collection in Portuguese, so the app he uses
to browse it ought to speak Portuguese too. Clicking the Portuguese flag at
the top right of the window relabels the whole interface; clicking the Union
Jack puts it back. The choice is remembered between sessions.

HOW IT WORKS, and why it works this way
---------------------------------------
The obvious way to localise a Tk app is to wrap every literal at the point it
is written - ttk.Button(text=_("Add stock")) - and rebuild the window when the
language changes. valves_gui.py has around two hundred such literals across
five tabs and a dozen dialogs, and rebuilding would throw away the selected
box, the current filters and every open popup.

So this module works the other way round. The interface is built in English
exactly as it always was, and then apply() walks the finished widget tree and
relabels what it finds: buttons, labels, checkbuttons, notebook tabs, treeview
headings, labelframe captions, menu entries and window titles. The English
text each widget was born with is remembered the first time it is seen
(see _remember), so switching back is exact rather than a reverse lookup -
which matters, because several English strings share one Portuguese word.

Two consequences worth knowing:

  * A widget created AFTER a switch is born in English. Dialogs therefore
    call i18n.apply(self) at the end of __init__ - one line each - and
    anything that rebuilds a menu re-applies too.

  * Text computed at runtime ("6 tracked individually", a status line, a
    SQL error) is not covered by the walk, because by the time it exists it
    is no longer a literal. The handful that matter are translated at the
    point they are built, through t() and tn(), which is why both are
    exported.

Nothing here touches the database. Type designations, box names, makers,
origins and the owner's own notes stay exactly as they were typed - a valve
is an EL84 in any language, and "Saco Pingo Doce" is the name of a bag, not
a word to be translated. Only the chrome moves.
"""

import json
import os
import tkinter as tk

LANGS = ("en", "pt")
_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".lang")

# Current language. Read it, don't write it - use set_language().
LANG = "en"

# Widget -> {option: original English text}, keyed by the Tk pathname string
# rather than the widget object so a destroyed widget's entry simply goes
# stale instead of keeping it alive.
_orig = {}
# (menu pathname, index) -> original English label
_menu_orig = {}
# Toplevel pathname -> original English title
_title_orig = {}


# --------------------------------------------------------------------------
# The dictionary
# --------------------------------------------------------------------------
# Keyed by the exact English string as it appears in the interface. A string
# with no entry here is left in English rather than mangled, so a missing
# translation degrades to "not translated yet" and never to nonsense.
#
# Valve terminology follows Portuguese electronics usage: valvula (valve),
# ampola for the envelope, "base" for the socket type, "grelha" for grid,
# "anodo" for anode, "filamento"/"aquecimento" for the heater.

PT = {
    # ---- window, tabs -----------------------------------------------------
    "Valves": "Válvulas",
    "Bases / Sockets": "Bases / Suportes",
    "Browse": "Explorar",
    "Repair Bench": "Bancada",
    "Docs": "Documentos",
    "Boxes": "Caixas",

    # ---- menus ------------------------------------------------------------
    "File": "Ficheiro",
    "Tools": "Ferramentas",
    "Help": "Ajuda",
    "Export spreadsheet...": "Exportar folha de cálculo...",
    "Export archive and tools (.zip)...": "Exportar arquivo e ferramentas (.zip)...",
    "Open database...": "Abrir base de dados...",
    "Quit": "Sair",
    "Collection summary": "Resumo da colecção",
    "What needs data": "O que falta preencher",
    "Possible duplicate types": "Possíveis tipos duplicados",
    "Check individual valve counts": "Verificar contagem de válvulas individuais",
    "Scan datasheet archive": "Analisar arquivo de folhas de dados",
    "Set archive folder...": "Definir pasta do arquivo...",
    "Create upload template...": "Criar modelo de importação...",
    "Import upload CSV...": "Importar CSV...",
    "Generate CSV-building prompt...": "Gerar instruções para construir CSV...",
    "Generate research prompt...": "Gerar instruções de pesquisa...",
    "Generate datasheet download prompt...":
        "Gerar instruções para descarregar folhas de dados...",
    "Apply researched data...": "Aplicar dados pesquisados...",
    "User guide": "Guia do utilizador",
    "Installation manual (PDF)": "Manual de instalação (PDF)",
    "User manual (PDF)": "Manual do utilizador (PDF)",
    "Technical manual (PDF)": "Manual técnico (PDF)",
    "Upgrade guide (PDF)": "Guia de actualização (PDF)",
    "About": "Acerca",

    # ---- buttons ----------------------------------------------------------
    "Add stock": "Adicionar existências",
    "Edit lot": "Editar lote",
    "Individual valves...": "Válvulas individuais...",
    "Take": "Retirar",
    "Move": "Mover",
    "Delete lot": "Eliminar lote",
    "Search": "Pesquisar",
    "Clear": "Limpar",
    "Clear all filters": "Limpar todos os filtros",
    "Advanced...": "Avançado...",
    "Open datasheet": "Abrir folha de dados",
    "Web search": "Pesquisar na web",
    "RadioMuseum": "RadioMuseum",
    "Manage information...": "Gerir informação...",
    "Edit parameters...": "Editar parâmetros...",
    "Save": "Guardar",
    "Cancel": "Cancelar",
    "Close": "Fechar",
    "OK": "OK",
    "Add": "Adicionar",
    "Remove": "Remover",
    "Delete": "Eliminar",
    "Edit": "Editar",
    "Refresh": "Actualizar",
    "Track individually": "Registar individualmente",
    "Record a test": "Registar um ensaio",
    "Test history": "Histórico de ensaios",
    "Add socket": "Adicionar suporte",
    "Take socket": "Retirar suporte",
    "Move socket": "Mover suporte",
    "Add document": "Adicionar documento",
    "Open": "Abrir",
    "Browse...": "Procurar...",

    # ---- filter captions --------------------------------------------------
    "Search": "Pesquisar",
    "Filters (cascading - options narrow as you pick)":
        "Filtros (em cascata - as opções estreitam à medida que escolhe)",
    "Text": "Texto",
    "Function": "Função",
    "Base": "Base",
    "Heater V": "Aquecimento V",
    "Heater A": "Aquecimento A",
    "Pa W": "Pa W",
    "Freq MHz": "Freq MHz",
    "Name contains": "Nome contém",
    "Category": "Categoria",
    "Family": "Família",
    "Confidence": "Confiança",
    "Variable-mu": "Mu variável",
    "Tested": "Ensaiada",
    "tested": "ensaiada",
    "untested": "por ensaiar",
    "(numeric fields accept  >20  <7  >=250)":
        "(campos numéricos aceitam  >20  <7  >=250)",
    "Double-click a row to see the individual valves in that lot":
        "Clique duas vezes numa linha para ver as válvulas individuais desse lote",

    # ---- table column headings -------------------------------------------
    "Box": "Caixa",
    "Pos": "Pos",
    "Type": "Tipo",
    "Type 1": "Tipo 1",
    "Type 2": "Tipo 2",
    "Match": "Equiv.",
    "Qty": "Qtd",
    "Qty held": "Qtd em stock",
    "Ind": "Ind",
    "Tstd": "Ens",
    "Maker": "Marca",
    "Condition": "Estado",
    "Origin": "Origem",
    "Htr V": "Aq. V",
    "Htr A": "Aq. A",
    "Sheet": "Folha",
    "Types": "Tipos",
    "Valve": "Válvula",
    "Serial": "Nº série",
    "Tests": "Ensaios",
    "Last test": "Último ensaio",
    "gm mA/V": "gm mA/V",
    "% nom": "% nom",
    "Ia mA": "Ia mA",
    "Verdict": "Veredicto",
    "Notes": "Notas",
    "Title": "Título",
    "Abstract": "Resumo",
    "Path": "Caminho",
    "URL": "URL",
    "Added": "Adicionado",
    "Va": "Va",
    "Pa": "Pa",
    "P.out": "P.saída",
    "Freq": "Freq",

    # ---- detail panel / misc labels --------------------------------------
    "Reference data": "Dados de referência",
    "Stock": "Existências",
    "Position": "Posição",
    "Manufacturer": "Fabricante",
    "Equivalents": "Equivalentes",
    "Typical use": "Utilização típica",
    "Datasheet": "Folha de dados",
    "No reference data yet.": "Ainda sem dados de referência.",
    "never tested": "nunca ensaiada",
    "not tracked individually": "não registada individualmente",
    # ---- repair bench -----------------------------------------------------
    "Type designation": "Designação do tipo",
    "Identify": "Identificar",
    "type a designation and click Identify":
        "escreva uma designação e clique em Identificar",
    "Got a valve out of a set you're repairing? Type its designation, find out "
    "what it is, and see what you've already got that could stand in for it.":
        "Tirou uma válvula de um aparelho que está a reparar? Escreva a "
        "designação, veja o que é, e o que já tem que possa substituí-la.",
    "In stock now (exact type or a listed equivalent)":
        "Em stock agora (tipo exacto ou equivalente listado)",
    "Possible substitutes in stock (same function, ratings within 50%)":
        "Substitutos possíveis em stock (mesma função, valores dentro de 50%)",
    "Similar types (may substitute, with modification)":
        "Tipos semelhantes (podem substituir, com alterações)",
    "Found in (circuit stage)": "Encontrada em (andar do circuito)",
    "Why": "Porquê",
    "Source": "Fonte",

    # ---- docs tab ---------------------------------------------------------
    "Filter": "Filtrar",
    "Add from file...": "Adicionar de ficheiro...",
    "Add from URL...": "Adicionar de URL...",
    "Edit title/about...": "Editar título/resumo...",
    "About / abstract": "Resumo",
    "General reference material - not tied to one valve type. Care-and-feeding "
    "guides, base wiring references, anything worth keeping alongside the "
    "collection.":
        "Material de referência geral - não ligado a um tipo de válvula. Guias "
        "de utilização, esquemas de ligação de bases, e tudo o que valha a "
        "pena guardar junto da colecção.",

    # ---- datasheet manager / parameter editor -----------------------------
    "Add to database": "Adicionar à base de dados",
    "Datasheet URL": "URL da folha de dados",
    "Download PDF": "Descarregar PDF",
    "Manage...": "Gerir...",
    "Copy prompt": "Copiar instruções",
    "Paste & apply...": "Colar e aplicar...",
    "Save + confirm": "Guardar + confirmar",

    # ---- reference field labels (detail panel, parameter editor) ----------
    "Pins": "Pinos",
    "Va max": "Va máx",
    "Va max V": "Va máx V",
    "Pa max": "Pa máx",
    "Pa max W": "Pa máx W",
    "Power out": "Potência saída",
    "Power out W": "Potência saída W",
    "Freq max": "Freq máx",
    "Freq max MHz": "Freq máx MHz",
    "gm": "gm",
    "mu": "mu",
    "Language": "Idioma",
}

TRANSLATIONS = {"en": {}, "pt": PT}


def t(s):
    """Translate one interface string, or return it unchanged if untranslated."""
    if s is None:
        return s
    return TRANSLATIONS.get(LANG, {}).get(s, s)


def tn(en, pt):
    """Pick between two literals by language.

    For text built at runtime, where there is no fixed English string to look
    up - a counted heading, a status line. Written at the call site so the
    Portuguese sits next to the English it belongs with.
    """
    return pt if LANG == "pt" else en


# --------------------------------------------------------------------------
# Remembering the English original
# --------------------------------------------------------------------------

def _remember(widget, option, value):
    """Record a widget's English text the first time it is seen, and return it.

    Everything is relabelled from this stored original rather than from
    whatever is on screen, so switching languages repeatedly cannot drift and
    two English strings sharing one Portuguese word still come back correctly.
    """
    key = (str(widget), option)
    if key not in _orig:
        _orig[key] = value
    return _orig[key]


def forget(widget):
    """Drop a destroyed widget's remembered text, and its children's.

    Tk reuses pathnames, so a stale entry would otherwise relabel an unrelated
    widget that happens to be born at the same path later on.
    """
    prefix = str(widget)
    for d in (_orig, _title_orig):
        for k in [k for k in d if (k[0] if isinstance(k, tuple) else k).startswith(prefix)]:
            del d[k]


# --------------------------------------------------------------------------
# Walking the tree
# --------------------------------------------------------------------------

_TEXT_CLASSES = ("TButton", "TLabel", "TCheckbutton", "TRadiobutton",
                 "TLabelframe", "Button", "Label", "Checkbutton",
                 "Radiobutton", "Labelframe", "LabelFrame")


def _apply_widget(w):
    """Relabel one widget in place, if it carries translatable text."""
    cls = w.winfo_class()
    if cls in _TEXT_CLASSES:
        try:
            cur = w.cget("text")
        except tk.TclError:
            return
        if isinstance(cur, str) and cur:
            try:
                w.configure(text=t(_remember(w, "text", cur)))
            except tk.TclError:
                pass
    elif cls == "TNotebook":
        for i, tab in enumerate(w.tabs()):
            cur = w.tab(tab, "text")
            if cur:
                w.tab(tab, text=t(_remember(w, f"tab{i}", cur)))
    elif cls == "Treeview":
        cols = list(w.cget("columns") or ())
        for col in list(cols) + ["#0"]:
            try:
                cur = w.heading(col, "text")
            except tk.TclError:
                continue
            if cur:
                w.heading(col, text=t(_remember(w, f"head{col}", cur)))
    # Combobox values are deliberately NOT translated. The facet pickers are
    # filled from the database - base codes, family names, makers, the
    # confidence flag - and those are the collection's own data, not the
    # app's chrome. "octal" stays "octal". The one list that is the app's own
    # (tested / untested) is built already-translated by its own tab, so it
    # needs nothing here either.


def _apply_menu(menu):
    """Relabel a menu and every submenu hanging off it."""
    try:
        last = menu.index("end")
    except tk.TclError:
        return
    if last is None:
        return
    for i in range(last + 1):
        if menu.type(i) == "separator":
            continue
        try:
            cur = menu.entrycget(i, "label")
        except tk.TclError:
            continue
        key = (str(menu), i)
        if key not in _menu_orig:
            _menu_orig[key] = cur
        menu.entryconfigure(i, label=t(_menu_orig[key]))
        # Only a cascade entry has a -menu option; asking a plain command for
        # one raises, and an unguarded raise here would abandon the rest of
        # the menu half-translated.
        try:
            sub = menu.entrycget(i, "menu")
        except tk.TclError:
            continue
        if sub:
            try:
                _apply_menu(menu.nametowidget(sub))
            except (KeyError, tk.TclError):
                pass


def apply(widget):
    """Relabel `widget` and everything inside it into the current language.

    Safe to call more than once, and safe on a tree that is partly translated
    already - every relabel goes through the remembered English original.
    Dialogs call this at the end of __init__ so a popup opened while the app
    is in Portuguese comes up in Portuguese.
    """
    _apply_widget(widget)
    if isinstance(widget, (tk.Tk, tk.Toplevel)):
        cur = widget.title()
        if cur:
            key = str(widget)
            if key not in _title_orig:
                _title_orig[key] = cur
            widget.title(t(_title_orig[key]))
        try:
            m = widget.cget("menu")
            if m:
                _apply_menu(widget.nametowidget(m))
        except (tk.TclError, KeyError):
            pass
    for child in widget.winfo_children():
        apply(child)


def set_language(lang, root=None):
    """Switch language, relabel everything reachable from `root`, and remember it."""
    global LANG
    if lang not in LANGS:
        return
    LANG = lang
    if root is not None:
        apply(root)
        for w in root.winfo_children():
            if isinstance(w, tk.Toplevel):
                apply(w)
    save_language()


def load_language():
    """Read the remembered language, defaulting to English."""
    global LANG
    try:
        with open(_STATE_FILE, encoding="utf-8") as f:
            lang = json.load(f).get("lang")
        if lang in LANGS:
            LANG = lang
    except Exception:
        pass          # no file, unreadable, corrupt - English is a fine default
    return LANG


def save_language():
    """Remember the current language for next time. Failure is not worth a dialog."""
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"lang": LANG}, f)
    except OSError:
        pass


# --------------------------------------------------------------------------
# The flag switch
# --------------------------------------------------------------------------

class FlagSwitch(tk.Frame):
    """Two small flags, top right: click one to put the app in that language.

    The flags are drawn with canvas primitives rather than loaded from image
    files, so there is nothing to install, nothing to find at runtime, and
    they render identically on every platform. They are small enough that a
    recognisable Union Jack is mostly a matter of getting the diagonals in
    the right order - white saltire first, red saltire over it, then the
    upright cross - and the Portuguese flag is a green/red field with a
    yellow armillary sphere suggested by two rings.
    """

    def __init__(self, master, on_change, **kw):
        super().__init__(master, **kw)
        self.on_change = on_change
        self.buttons = {}
        for lang, drawer, tip in (("en", self._draw_uk, "English"),
                                  ("pt", self._draw_pt, "Português")):
            c = tk.Canvas(self, width=30, height=20, highlightthickness=2,
                          cursor="hand2", takefocus=0)
            c.pack(side="left", padx=(0, 5))
            drawer(c)
            c.bind("<Button-1>", lambda _e, l=lang: self._pick(l))
            self._tooltip(c, tip)
            self.buttons[lang] = c
        self.highlight()

    def _pick(self, lang):
        if lang != LANG:
            self.on_change(lang)
        self.highlight()

    def highlight(self):
        """Ring the flag for the language now in use."""
        for lang, c in self.buttons.items():
            c.configure(highlightbackground="#1a5fb4" if lang == LANG else "#cccccc",
                        highlightcolor="#1a5fb4" if lang == LANG else "#cccccc")

    @staticmethod
    def _tooltip(widget, text):
        """A plain hover label - Tk has no tooltip of its own."""
        tip = {"win": None}

        def show(_e):
            if tip["win"]:
                return
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height() + 2
            w = tk.Toplevel(widget)
            w.wm_overrideredirect(True)
            w.wm_geometry(f"+{x}+{y}")
            tk.Label(w, text=text, background="#ffffe0", relief="solid",
                     borderwidth=1, padx=4).pack()
            tip["win"] = w

        def hide(_e):
            if tip["win"]:
                tip["win"].destroy()
                tip["win"] = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    @staticmethod
    def _draw_uk(c):
        """Union Jack: blue field, white then red saltires, white then red cross."""
        c.create_rectangle(0, 0, 30, 20, fill="#012169", outline="")
        for x0, y0, x1, y1 in ((0, 0, 30, 20), (30, 0, 0, 20)):
            c.create_line(x0, y0, x1, y1, fill="white", width=5)
        for x0, y0, x1, y1 in ((0, 0, 30, 20), (30, 0, 0, 20)):
            c.create_line(x0, y0, x1, y1, fill="#C8102E", width=2)
        c.create_rectangle(0, 7, 30, 13, fill="white", outline="")
        c.create_rectangle(11, 0, 19, 20, fill="white", outline="")
        c.create_rectangle(0, 8.5, 30, 11.5, fill="#C8102E", outline="")
        c.create_rectangle(12.5, 0, 17.5, 20, fill="#C8102E", outline="")

    @staticmethod
    def _draw_pt(c):
        """Portugal: green hoist, red fly, armillary sphere on the join."""
        c.create_rectangle(0, 0, 12, 20, fill="#006600", outline="")
        c.create_rectangle(12, 0, 30, 20, fill="#FF0000", outline="")
        c.create_oval(7, 5, 17, 15, outline="#FFD700", width=2)
        c.create_oval(9.5, 5, 14.5, 15, outline="#FFD700", width=1)
        c.create_rectangle(10, 8, 14, 12, fill="white", outline="#003399")
