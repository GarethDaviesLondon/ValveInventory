#!/usr/bin/env python3
"""
build_getting_started.py - generates docs/GETTING_STARTED_EN_PT.pdf, the
bilingual "first launch on Windows" guide.

    python3 docs/build_getting_started.py

Requires reportlab (pip install reportlab), like build_manuals.py - not a
runtime dependency of the tool itself.

Why this exists alongside the manuals. INSTALLATION_MANUAL.pdf covers every
platform and every way of getting the files; this covers exactly one path -
somebody on Windows who has been sent the exported zip and wants the window
open. It is written for a reader who is comfortable with a soldering iron and
not with a command line, so it spends most of its length on the one thing that
actually stops people: typing shell commands into the Python prompt.

Layout. Everything is English on the left, Portuguese on the right, aligned
piece by piece rather than page by page: pair() puts one English flowable list
and its Portuguese counterpart into a single two-column table row, so the two
languages stay level all the way down even where one is longer than the other.
Anything that is language-neutral or genuinely full width (the title block, the
two console illustrations) is appended to the story directly instead.
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle,
    KeepTogether,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "GETTING_STARTED_EN_PT.pdf"

# A4, because the reader is in Portugal and will print this.
PAGE = A4
LMARGIN = RMARGIN = 15 * mm
TMARGIN = 16 * mm
BMARGIN = 16 * mm
FRAME_W = PAGE[0] - LMARGIN - RMARGIN
GUTTER = 7 * mm
COL_W = FRAME_W / 2.0
# Usable width inside a pair() cell, for anything that has to be given an
# explicit width of its own - i.e. every panel, since reportlab paints a
# Paragraph backColor without reserving room for its padding and ignores
# one on a Preformatted entirely. Panels are therefore single-cell tables.
COL_INNER = COL_W - GUTTER / 2.0

INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#666666")
RULE = colors.HexColor("#cfcfc9")
PANEL = colors.HexColor("#f4f4f2")
GOOD = colors.HexColor("#1f7a3d")
BAD = colors.HexColor("#a01818")

_base = getSampleStyleSheet()

S = {
    "title": ParagraphStyle("title", parent=_base["Title"], fontSize=21,
                            leading=25, spaceAfter=2, textColor=INK),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Normal"], fontSize=11,
                               leading=15, alignment=TA_CENTER, textColor=GREY,
                               spaceAfter=2),
    "collabel": ParagraphStyle("collabel", parent=_base["Normal"], fontSize=8,
                               leading=10, textColor=GREY, spaceAfter=0),
    "h1": ParagraphStyle("h1", parent=_base["Heading1"], fontSize=13,
                         leading=16, spaceBefore=2, spaceAfter=5, textColor=INK),
    "h2": ParagraphStyle("h2", parent=_base["Heading2"], fontSize=10.5,
                         leading=13, spaceBefore=2, spaceAfter=3, textColor=INK),
    "body": ParagraphStyle("body", parent=_base["Normal"], fontSize=9.3,
                           leading=12.6, spaceAfter=6, alignment=TA_LEFT,
                           textColor=INK),
    "bullet": ParagraphStyle("bullet", parent=_base["Normal"], fontSize=9.3,
                             leading=12.6, spaceAfter=3, leftIndent=10,
                             bulletIndent=1, textColor=INK),
    "note": ParagraphStyle("note", parent=_base["Normal"], fontSize=8.8,
                           leading=12, spaceAfter=0, textColor=colors.HexColor("#333333")),
    "code": ParagraphStyle("code", parent=_base["Code"], fontSize=8.4,
                           leading=11, leftIndent=0, spaceBefore=0, spaceAfter=0,
                           textColor=INK),
    "caption": ParagraphStyle("caption", parent=_base["Normal"], fontSize=8,
                              leading=10.5, textColor=GREY, spaceAfter=0),
    "conlabel": ParagraphStyle("conlabel", parent=_base["Normal"], fontSize=9,
                               leading=12, spaceAfter=3),
}


# ------------------------------------------------------------------ pieces
# Small wrappers so the content section below reads as content and not as
# reportlab plumbing. Each returns a list of flowables, which is what pair()
# wants for a column cell.

def h1(text):
    return [Paragraph(text, S["h1"])]


def h2(text):
    return [Paragraph(text, S["h2"])]


def p(*paras):
    return [Paragraph(t, S["body"]) for t in paras]


def panel(flow, width, bg, pad=6, edge=None, space=(3, 7)):
    """One tinted box: content, padding and background in a single-cell table.

    Everything visual in this document goes through here - a table cell is the
    only construct reportlab both paints and measures, so nothing can overlap
    the block that follows it.
    """
    t = Table([[flow]], colWidths=[width])
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad - 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 1),
    ]
    if edge is not None:
        style.append(("BOX", (0, 0), (-1, -1), 0.9, edge))
    t.setStyle(TableStyle(style))
    return [Spacer(1, space[0]), t, Spacer(1, space[1])]


def note(text):
    return panel(Paragraph(text, S["note"]), COL_INNER, PANEL)


def bullets(items):
    return [Paragraph(f"\u2022&nbsp;&nbsp;{i}", S["bullet"]) for i in items]


def code(text):
    return panel(Preformatted(text, S["code"]), COL_INNER, PANEL, pad=5,
                 space=(2, 7))


def gap(h=4):
    return [Spacer(1, h)]


def paras(en, pt):
    """A run of one-paragraph rows - English and Portuguese given as matching
    lists. Each paragraph gets its own row so the page can break between them;
    a row itself never splits (see pair)."""
    assert len(en) == len(pt)
    return [pair(p(a), p(b)) for a, b in zip(en, pt)]


def pair(en, pt):
    """One row of the guide: English flowables left, Portuguese right.

    Padding is asymmetric so the gutter sits between the columns rather than
    inside them, and a hairline before the right-hand cell carries the
    English/Portuguese split down the page.
    """
    t = Table([[en, pt]], colWidths=[COL_W, COL_W])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), GUTTER / 2.0),
        ("LEFTPADDING", (1, 0), (1, 0), GUTTER / 2.0),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("LINEBEFORE", (1, 0), (1, 0), 0.4, RULE),
    ]))
    # Deliberately not splitInRow: reportlab 5.x loops rather than splitting a
    # row whose cells hold nested tables, which every panel here is. Rows are
    # kept short instead - see paras() - so a break always has somewhere to go.
    return t


def step(n, en_title, pt_title, *rows):
    """A numbered step: its bilingual heading, kept with the first row that
    follows it, then the rest of the rows."""
    head = pair(h1(f"{n}. {en_title}"), h1(f"{n}. {pt_title}"))
    out = [Spacer(1, 9)]
    if rows:
        out.append(KeepTogether([head, rows[0]]))
        out.extend(rows[1:])
    else:
        out.append(head)
    return out


def console(title_en, title_pt, lines, good):
    """A full-width mock-up of one of the two black windows, captioned in both
    languages. Screenshots would age badly and would only exist in one
    language; this stays legible in print and says the same thing twice."""
    edge = GOOD if good else BAD
    mark = "RIGHT / CORRECTO" if good else "WRONG / ERRADO"
    head = Paragraph(
        f'<font color="{edge.hexval()}"><b>{mark}</b></font> &nbsp;&nbsp;'
        f'<b>{title_en}</b>', S["conlabel"])
    head_pt = Paragraph(f'<i>{title_pt}</i>', S["caption"])
    body = Preformatted(lines, ParagraphStyle(
        "con", parent=S["code"], textColor=colors.HexColor("#e8e8e8"),
        fontSize=8, leading=10.5))
    screen = panel(body, FRAME_W - 14, colors.HexColor("#101010"), pad=7,
                   space=(0, 0))[1]
    t = Table([[head], [head_pt], [screen]], colWidths=[FRAME_W])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING", (0, 2), (0, 2), 5),
        ("BOTTOMPADDING", (0, 2), (0, 2), 7),
        ("BOX", (0, 0), (-1, -1), 0.9, edge),
    ]))
    return KeepTogether([Spacer(1, 6), t, Spacer(1, 5)])


def trouble(symptom, en, pt):
    """One troubleshooting entry: the symptom full width (it is the same in
    both languages - an error message is not translated), then the two
    explanations side by side."""
    sym = panel(Preformatted(symptom, S["code"]), FRAME_W,
                colors.HexColor("#ebebe6"), pad=5, space=(0, 0))[1]
    return KeepTogether([Spacer(1, 8), sym, Spacer(1, 5), pair(p(en), p(pt))])


# ------------------------------------------------------------------ page
def decorate(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(LMARGIN, BMARGIN - 9 * mm,
                      "Valve Inventory - Getting started on Windows / "
                      "Como come\u00e7ar no Windows")
    canvas.drawRightString(PAGE[0] - RMARGIN, BMARGIN - 9 * mm,
                           f"{doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(LMARGIN, BMARGIN - 6.5 * mm, PAGE[0] - RMARGIN, BMARGIN - 6.5 * mm)
    canvas.restoreState()


# ------------------------------------------------------------------ content
def story():
    s = []

    # --- title block, full width -----------------------------------------
    s.append(Paragraph("Valve Inventory", ParagraphStyle(
        "t", parent=S["title"], alignment=TA_CENTER)))
    s.append(Paragraph(
        "Getting started on Windows &nbsp;|&nbsp; Como come&ccedil;ar no Windows",
        S["subtitle"]))
    s.append(Paragraph(
        "English on the left, portugu&ecirc;s &agrave; direita.",
        ParagraphStyle("t3", parent=S["caption"], alignment=TA_CENTER)))
    s.append(Spacer(1, 10))
    s.append(pair([Paragraph("<b>ENGLISH</b>", S["collabel"])],
                  [Paragraph("<b>PORTUGU&Ecirc;S</b>", S["collabel"])]))
    s.append(Spacer(1, 6))

    s += paras(
        ["This is the short route from the zip file you downloaded to the "
          "program window open on your screen. It only covers Windows, and it "
          "assumes somebody sent you the exported copy of the collection "
          "rather than you fetching it from GitHub.",
         "You do not need to know anything about programming. There are two "
         "commands in the whole guide, and if the first step works you will "
         "not have to type either of them."],
        ["Este &eacute; o caminho curto entre o ficheiro zip que descarregou e "
          "a janela do programa aberta no seu ecr&atilde;. S&oacute; cobre o "
          "Windows e parte do princ&iacute;pio de que algu&eacute;m lhe enviou "
          "a c&oacute;pia exportada da colec&ccedil;&atilde;o, em vez de a ter "
          "ido buscar ao GitHub.",
         "N&atilde;o precisa de saber nada de programa&ccedil;&atilde;o. H&aacute; "
         "dois comandos em todo o guia e, se o primeiro passo resultar, n&atilde;o "
         "ter&aacute; de escrever nenhum deles."])

    # --- 0. what you need -------------------------------------------------
    s += step(
        0, "What you need", "O que &eacute; preciso",
        pair(bullets([
                "A Windows PC.",
                "<b>Python 3.8 or newer.</b> If you already installed Python "
                "3.13, that is done - nothing more to install.",
                "The file <font face=\"Courier\">valve-inventory.zip</font> "
                "that you downloaded from Dropbox.",
                "About ten minutes.",
             ]),
             bullets([
                "Um PC com Windows.",
                "<b>Python 3.8 ou mais recente.</b> Se j&aacute; instalou o "
                "Python 3.13, est&aacute; feito - n&atilde;o h&aacute; mais "
                "nada para instalar.",
                "O ficheiro <font face=\"Courier\">valve-inventory.zip</font> "
                "que descarregou da Dropbox.",
                "Cerca de dez minutos.",
             ])),
        pair(note("Nothing else is needed. The database is a single file that "
                  "Python already knows how to read - there is no server to "
                  "install, no account to create and nothing goes over the "
                  "internet."),
             note("N&atilde;o &eacute; preciso mais nada. A base de dados "
                  "&eacute; um &uacute;nico ficheiro que o Python j&aacute; "
                  "sabe ler - n&atilde;o h&aacute; servidor para instalar, nem "
                  "conta para criar, e nada passa pela internet.")))

    # --- 1. extract -------------------------------------------------------
    s += step(
        1, "Unpack the zip first", "Extrair primeiro o zip",
        pair(p("When you double-click the zip, WinRAR (or Windows itself) shows "
               "you what is inside. That is only a <b>preview</b> - the files "
               "are still packed and the program will not run from there."),
             p("Quando faz duplo clique no zip, o WinRAR (ou o pr&oacute;prio "
               "Windows) mostra-lhe o que est&aacute; l&aacute; dentro. Isso &eacute; "
               "apenas uma <b>pr&eacute;-visualiza&ccedil;&atilde;o</b> - os "
               "ficheiros continuam compactados e o programa n&atilde;o corre "
               "a partir da&iacute;.")),
        pair(p("<b>Do this instead:</b>"), p("<b>Fa&ccedil;a antes assim:</b>")),
        pair(bullets([
                "Right-click <font face=\"Courier\">valve-inventory.zip</font> "
                "in the Downloads folder.",
                "Choose <b>Extract to valve-inventory\\</b> (WinRAR) or "
                "<b>Extract All...</b> (Windows).",
                "When it asks where, put it somewhere short and easy to type - "
                "<font face=\"Courier\">C:\\valve-inventory</font> is ideal.",
                "Wait for it to finish. It is a large archive if the datasheets "
                "came with it.",
             ]),
             bullets([
                "Clique com o bot&atilde;o direito em "
                "<font face=\"Courier\">valve-inventory.zip</font>, na pasta "
                "Transfer&ecirc;ncias.",
                "Escolha <b>Extrair para valve-inventory\\</b> (WinRAR) ou "
                "<b>Extrair Tudo...</b> (Windows).",
                "Quando perguntar onde, escolha um s&iacute;tio curto e "
                "f&aacute;cil de escrever - "
                "<font face=\"Courier\">C:\\valve-inventory</font> &eacute; o ideal.",
                "Espere que termine. &Eacute; um arquivo grande se vier com as "
                "folhas de dados.",
             ])),
        pair(note("<b>Why it matters:</b> opening a file from inside WinRAR "
                  "copies it to a temporary folder on its own, without the "
                  "other files it needs. The program will fail there even when "
                  "everything is correct."),
             note("<b>Porque &eacute; importante:</b> abrir um ficheiro de "
                  "dentro do WinRAR copia-o sozinho para uma pasta "
                  "tempor&aacute;ria, sem os outros ficheiros de que precisa. "
                  "O programa falha a&iacute; mesmo quando est&aacute; tudo bem.")))

    # --- 2. check the folder ---------------------------------------------
    s += step(
        2, "Check the folder", "Confirmar a pasta",
        pair(p("Open <font face=\"Courier\">C:\\valve-inventory</font> in File "
               "Explorer. You should see these among the files:"),
             p("Abra <font face=\"Courier\">C:\\valve-inventory</font> no "
               "Explorador de Ficheiros. Deve ver estes ficheiros, entre outros:")),
        pair(code("run.bat\nvalves_gui.py\nvalves.db\ndocs\\\ndata\\"),
             code("run.bat\nvalves_gui.py\nvalves.db\ndocs\\\ndata\\")),
        pair(p("If instead you see one folder called "
               "<font face=\"Courier\">valve-inventory</font> with everything "
               "inside it, that is fine - just go into it. The folder you want "
               "is the one that directly contains "
               "<font face=\"Courier\">run.bat</font>."),
             p("Se em vez disso vir uma pasta chamada "
               "<font face=\"Courier\">valve-inventory</font> com tudo "
               "l&aacute; dentro, n&atilde;o faz mal - basta entrar nela. A "
               "pasta certa &eacute; aquela que cont&eacute;m directamente o "
               "<font face=\"Courier\">run.bat</font>.")))

    # --- 3. run it --------------------------------------------------------
    s += step(
        3, "Start it - the easy way", "Arrancar - a maneira f&aacute;cil",
        pair(p("<b>Double-click <font face=\"Courier\">run.bat</font>.</b> "
               "That is the whole step."),
             p("<b>Fa&ccedil;a duplo clique em "
               "<font face=\"Courier\">run.bat</font>.</b> &Eacute; s&oacute; isso.")),
        pair(p("A black window appears for a second and then the program window "
               "opens. Leave the black window alone - closing it closes the "
               "program."),
             p("Aparece uma janela preta durante um segundo e depois abre a "
               "janela do programa. Deixe a janela preta em paz - "
               "fech&aacute;-la fecha o programa.")),
        pair(bullets([
                "If Windows shows a blue <b>\u201cWindows protected your PC\u201d</b> "
                "box: click <b>More info</b>, then <b>Run anyway</b>. It says "
                "that about any file downloaded from the internet.",
                "If the black window appears and disappears with an error you "
                "cannot read, or nothing happens at all, go to step 5.",
             ]),
             bullets([
                "Se o Windows mostrar a caixa azul <b>\u201cO Windows protegeu "
                "o seu PC\u201d</b>: clique em <b>Mais informa&ccedil;&otilde;es</b> "
                "e depois em <b>Executar mesmo assim</b>. Ele diz isso de "
                "qualquer ficheiro vindo da internet.",
                "Se a janela preta aparecer e desaparecer com um erro que "
                "n&atilde;o consegue ler, ou se n&atilde;o acontecer nada, "
                "v&aacute; para o passo 5.",
             ])))

    # --- 4. Portuguese ----------------------------------------------------
    s += step(
        4, "Put the program in Portuguese", "Colocar o programa em portugu&ecirc;s",
        pair(p("Top right of the window there are two small flags. Click the "
               "<b>Portuguese flag</b> and the whole interface changes "
               "language. It remembers your choice the next time you open it."),
             p("No canto superior direito da janela h&aacute; duas bandeiras "
               "pequenas. Clique na <b>bandeira portuguesa</b> e toda a "
               "interface muda de idioma. A escolha fica guardada para a "
               "pr&oacute;xima vez que abrir.")),
        pair(p("Then <b>Ajuda &gt; Guia do utilizador</b> gives you a "
               "walkthrough of the program itself, in Portuguese - what this "
               "guide deliberately does not cover."),
             p("Depois, <b>Ajuda &gt; Guia do utilizador</b> d&aacute;-lhe um "
               "percurso pelo pr&oacute;prio programa, em portugu&ecirc;s - "
               "aquilo que este guia de prop&oacute;sito n&atilde;o cobre.")))

    # --- 5. the two black windows ----------------------------------------
    s += step(
        5, "The two black windows - this is the important part",
        "As duas janelas pretas - esta &eacute; a parte importante",
        pair(p("If step 3 did not work you will need to type a command, and "
               "this is where it goes wrong for almost everybody. Windows has "
               "<b>two</b> black windows that look nearly identical and they "
               "are not interchangeable."),
             p("Se o passo 3 n&atilde;o resultou, vai ter de escrever um "
               "comando - e &eacute; aqui que quase toda a gente se engana. O "
               "Windows tem <b>duas</b> janelas pretas quase iguais, e "
               "n&atilde;o servem para o mesmo.")))
    s.append(console(
        "The Python window - do NOT type commands here",
        "A janela do Python - N&Atilde;O escreva comandos aqui",
        'Python 3.13.14 (tags/v3.13.14) [MSC v.1944 64 bit (AMD64)] on win32\n'
        'Type "help", "copyright", "credits" or "license" for more information.\n'
        '>>> python valves_gui.py\n'
        '  File "<python-input-4>", line 1\n'
        '    python valves_gui.py\n'
        '           ^^^^^^^^^^^^\n'
        'SyntaxError: invalid syntax',
        good=False))
    s += paras(
        ["You can tell it by the <font face=\"Courier\"><b>&gt;&gt;&gt;</b></font> "
          "prompt and the line about \u201chelp, copyright, credits\u201d. This "
          "window is Python itself: it only understands the Python language, "
          "not commands. Typing "
          "<font face=\"Courier\">python valves_gui.py</font> here gives "
          "<font face=\"Courier\">SyntaxError</font>; typing "
          "<font face=\"Courier\">bash</font> gives "
          "<font face=\"Courier\">NameError</font>. Nothing is broken - it is "
          "simply the wrong window.",
         "<b>To leave it,</b> type <font face=\"Courier\">exit()</font> and "
         "press Enter, or just close the window."],
        ["Reconhece-a pela linha de comandos "
          "<font face=\"Courier\"><b>&gt;&gt;&gt;</b></font> e pela frase sobre "
          "\u201chelp, copyright, credits\u201d. Esta janela &eacute; o "
          "pr&oacute;prio Python: s&oacute; percebe a linguagem Python, "
          "n&atilde;o comandos. Escrever aqui "
          "<font face=\"Courier\">python valves_gui.py</font> d&aacute; "
          "<font face=\"Courier\">SyntaxError</font>; escrever "
          "<font face=\"Courier\">bash</font> d&aacute; "
          "<font face=\"Courier\">NameError</font>. N&atilde;o est&aacute; nada "
          "avariado - &eacute; apenas a janela errada.",
         "<b>Para sair,</b> escreva <font face=\"Courier\">exit()</font> e "
         "carregue em Enter, ou feche simplesmente a janela."])
    s.append(console(
        "The Command Prompt - this is where commands go",
        "A Linha de Comandos - &eacute; aqui que os comandos se escrevem",
        'Microsoft Windows [Version 10.0.19045.4529]\n'
        '(c) Microsoft Corporation. All rights reserved.\n'
        '\n'
        'C:\\Users\\Hernani> cd C:\\valve-inventory\n'
        '\n'
        'C:\\valve-inventory> python valves_gui.py',
        good=True))
    s.append(pair(
        p("You can tell it by the prompt ending in "
          "<font face=\"Courier\"><b>&gt;</b></font> and showing a folder, like "
          "<font face=\"Courier\">C:\\valve-inventory&gt;</font>. There is no "
          "<font face=\"Courier\">&gt;&gt;&gt;</font> and no mention of "
          "copyright or credits."),
        p("Reconhece-a pela linha que termina em "
          "<font face=\"Courier\"><b>&gt;</b></font> e mostra uma pasta, como "
          "<font face=\"Courier\">C:\\valve-inventory&gt;</font>. N&atilde;o "
          "tem <font face=\"Courier\">&gt;&gt;&gt;</font> nem fala de "
          "copyright ou credits.")))

    # --- 6. command prompt ------------------------------------------------
    s += step(
        6, "Starting it from the Command Prompt",
        "Arrancar a partir da Linha de Comandos",
        pair(p("<b>a.</b> Press the <b>Windows key</b>, type "
               "<font face=\"Courier\">cmd</font> and press <b>Enter</b>. The "
               "Command Prompt opens - check it looks like the green box "
               "above, not the red one."),
             p("<b>a.</b> Carregue na <b>tecla Windows</b>, escreva "
               "<font face=\"Courier\">cmd</font> e carregue em <b>Enter</b>. "
               "Abre a Linha de Comandos - confirme que se parece com a caixa "
               "verde acima e n&atilde;o com a vermelha.")),
        pair(p("<b>b.</b> Go to the folder. Type this and press Enter:"),
             p("<b>b.</b> V&aacute; para a pasta. Escreva isto e carregue em Enter:")),
        pair(code("cd C:\\valve-inventory"), code("cd C:\\valve-inventory")),
        pair(p("The prompt should now read "
               "<font face=\"Courier\">C:\\valve-inventory&gt;</font>. If it "
               "does not, do not go on - see step 8."),
             p("A linha deve passar a mostrar "
               "<font face=\"Courier\">C:\\valve-inventory&gt;</font>. Se "
               "n&atilde;o mostrar, n&atilde;o avance - veja o passo 8.")),
        pair(p("<b>c.</b> Start the program:"),
             p("<b>c.</b> Arranque o programa:")),
        pair(code("python valves_gui.py"), code("python valves_gui.py")),
        pair(p("If Windows answers that "
               "<font face=\"Courier\">python</font> is not recognised, use "
               "this instead - it is the launcher that always comes with "
               "Python on Windows:"),
             p("Se o Windows responder que "
               "<font face=\"Courier\">python</font> n&atilde;o &eacute; "
               "reconhecido, use antes isto - &eacute; o lan&ccedil;ador que "
               "vem sempre com o Python no Windows:")),
        pair(code("py valves_gui.py"), code("py valves_gui.py")),
        pair(note("Tip: instead of typing the folder path, open the folder in "
                  "File Explorer, click the address bar, type "
                  "<font face=\"Courier\">cmd</font> and press Enter. A Command "
                  "Prompt opens already in that folder, so you can skip "
                  "step 6b entirely."),
             note("Sugest&atilde;o: em vez de escrever o caminho da pasta, abra "
                  "a pasta no Explorador de Ficheiros, clique na barra de "
                  "endere&ccedil;o, escreva <font face=\"Courier\">cmd</font> e "
                  "carregue em Enter. Abre uma Linha de Comandos j&aacute; "
                  "nessa pasta, e assim pode saltar o passo 6b.")))

    # --- 7. database ------------------------------------------------------
    s += step(
        7, "If the collection looks empty", "Se a colec&ccedil;&atilde;o aparecer vazia",
        pair(p("The collection lives in <font face=\"Courier\">valves.db</font>. "
               "If that file is in the folder, you have nothing to do here - "
               "the program opens it by itself."),
             p("A colec&ccedil;&atilde;o est&aacute; no ficheiro "
               "<font face=\"Courier\">valves.db</font>. Se esse ficheiro "
               "estiver na pasta, n&atilde;o tem nada a fazer aqui - o "
               "programa abre-o sozinho.")),
        pair(p("If it is missing, or the program opens with no valves in it, "
               "rebuild it from the text copy in "
               "<font face=\"Courier\">data\\</font>. In the Command Prompt, in "
               "the same folder:"),
             p("Se faltar, ou se o programa abrir sem nenhuma v&aacute;lvula, "
               "reconstrua-o a partir da c&oacute;pia em texto que est&aacute; "
               "em <font face=\"Courier\">data\\</font>. Na Linha de Comandos, "
               "na mesma pasta:")),
        pair(code("python snapshot.py --restore\npython test_smoke.py"),
             code("python snapshot.py --restore\npython test_smoke.py")),
        pair(p("The second command checks everything fits together and should "
               "end with <font face=\"Courier\">all checks passed</font>."),
             p("O segundo comando verifica se est&aacute; tudo bem e deve "
               "terminar com <font face=\"Courier\">all checks passed</font>.")),
        pair(note("<font face=\"Courier\">valves.db already exists</font> is not "
                  "an error - it means the database is already there and the "
                  "program is refusing to overwrite it. Good news: skip this "
                  "step."),
             note("<font face=\"Courier\">valves.db already exists</font> "
                  "n&atilde;o &eacute; um erro - quer dizer que a base de dados "
                  "j&aacute; l&aacute; est&aacute; e o programa recusa-se a "
                  "escrever por cima. Boa not&iacute;cia: salte este passo.")))

    # --- 8. troubleshooting ----------------------------------------------
    s += step(
        8, "When something goes wrong", "Quando alguma coisa corre mal",
        pair(p("The message is printed in English by Windows and by Python, so "
               "it is shown here as you will see it on screen."),
             p("A mensagem &eacute; escrita em ingl&ecirc;s pelo Windows e pelo "
               "Python, por isso aparece aqui tal como a ver&aacute; no "
               "ecr&atilde;.")))

    s.append(trouble(
        "SyntaxError: invalid syntax\nNameError: name 'bash' is not defined",
        "You are typing into the Python window (the one with "
        "<font face=\"Courier\">&gt;&gt;&gt;</font>). Type "
        "<font face=\"Courier\">exit()</font>, press Enter, and start again "
        "from step 6a in the Command Prompt.",
        "Est&aacute; a escrever na janela do Python (a que tem "
        "<font face=\"Courier\">&gt;&gt;&gt;</font>). Escreva "
        "<font face=\"Courier\">exit()</font>, carregue em Enter e recomece no "
        "passo 6a, na Linha de Comandos."))

    s.append(trouble(
        "'python' is not recognized as an internal or external command",
        "Use <font face=\"Courier\">py valves_gui.py</font> instead. If that "
        "also fails, reinstall Python and tick <b>Add python.exe to PATH</b> on "
        "the first screen of the installer.",
        "Use antes <font face=\"Courier\">py valves_gui.py</font>. Se tamb&eacute;m "
        "falhar, reinstale o Python e marque <b>Add python.exe to PATH</b> no "
        "primeiro ecr&atilde; do instalador."))

    s.append(trouble(
        "The Microsoft Store opens instead of Python",
        "Windows is intercepting the name. Open <b>Settings &gt; Apps &gt; "
        "Advanced app settings &gt; App execution aliases</b> and turn "
        "<b>off</b> the two entries for "
        "<font face=\"Courier\">python.exe</font> and "
        "<font face=\"Courier\">python3.exe</font>. Or simply use "
        "<font face=\"Courier\">py</font>, which is never intercepted.",
        "O Windows est&aacute; a interceptar o nome. Abra "
        "<b>Defini&ccedil;&otilde;es &gt; Aplica&ccedil;&otilde;es &gt; "
        "Defini&ccedil;&otilde;es avan&ccedil;adas &gt; Aliases de "
        "execu&ccedil;&atilde;o de aplica&ccedil;&otilde;es</b> e "
        "<b>desligue</b> as duas entradas de "
        "<font face=\"Courier\">python.exe</font> e "
        "<font face=\"Courier\">python3.exe</font>. Ou use simplesmente "
        "<font face=\"Courier\">py</font>, que nunca &eacute; interceptado."))

    s.append(trouble(
        "The system cannot find the path specified",
        "The folder name in your <font face=\"Courier\">cd</font> command does "
        "not match the real one. Copy the exact path from the File Explorer "
        "address bar. If the files are on another drive, use "
        "<font face=\"Courier\">cd /d D:\\valve-inventory</font> - without "
        "<font face=\"Courier\">/d</font> the drive does not change.",
        "O nome da pasta no seu comando <font face=\"Courier\">cd</font> "
        "n&atilde;o corresponde ao real. Copie o caminho exacto da barra de "
        "endere&ccedil;o do Explorador de Ficheiros. Se os ficheiros estiverem "
        "noutra unidade, use <font face=\"Courier\">cd /d D:\\valve-inventory</font> "
        "- sem <font face=\"Courier\">/d</font> a unidade n&atilde;o muda."))

    s.append(trouble(
        "can't open file '...valves_gui.py': [Errno 2] No such file or directory",
        "You are in the wrong folder. Type <font face=\"Courier\">dir</font> and "
        "press Enter: if <font face=\"Courier\">valves_gui.py</font> is not in "
        "the list, repeat step 6b.",
        "Est&aacute; na pasta errada. Escreva <font face=\"Courier\">dir</font> "
        "e carregue em Enter: se <font face=\"Courier\">valves_gui.py</font> "
        "n&atilde;o estiver na lista, repita o passo 6b."))

    s.append(trouble(
        "ModuleNotFoundError: No module named 'tkinter'",
        "Rare on Windows. Reinstall Python and make sure "
        "<b>tcl/tk and IDLE</b> is ticked in the optional features screen.",
        "Raro no Windows. Reinstale o Python e certifique-se de que "
        "<b>tcl/tk and IDLE</b> est&aacute; marcado no ecr&atilde; das "
        "funcionalidades opcionais."))

    s.append(trouble(
        "ModuleNotFoundError: No module named 'openpyxl'",
        "Only needed to export a spreadsheet. Either avoid that menu item, or "
        "run <font face=\"Courier\">pip install openpyxl</font> once, in the "
        "Command Prompt.",
        "S&oacute; &eacute; preciso para exportar uma folha de c&aacute;lculo. "
        "Ou evite essa op&ccedil;&atilde;o do menu, ou execute uma vez "
        "<font face=\"Courier\">pip install openpyxl</font> na Linha de "
        "Comandos."))

    s.append(trouble(
        "The window opens and closes at once, or nothing happens",
        "Run it from the Command Prompt (step 6) so the error stays on screen "
        "instead of vanishing with the window, then read the last line.",
        "Execute-o a partir da Linha de Comandos (passo 6) para que o erro "
        "fique no ecr&atilde; em vez de desaparecer com a janela, e leia depois "
        "a &uacute;ltima linha."))

    # --- 9. manuals -------------------------------------------------------
    s += step(
        9, "The rest of the documentation", "A restante documenta&ccedil;&atilde;o",
        pair(p("The <font face=\"Courier\">docs\\</font> folder has the full "
               "manuals, each in both languages. The Portuguese ones end in "
               "<font face=\"Courier\">_PT.pdf</font>:"),
             p("A pasta <font face=\"Courier\">docs\\</font> tem os manuais "
               "completos, cada um nos dois idiomas. Os portugueses terminam em "
               "<font face=\"Courier\">_PT.pdf</font>:")),
        pair(bullets([
                "<font face=\"Courier\">INSTALLATION_MANUAL_PT.pdf</font> - "
                "installing, on any system.",
                "<font face=\"Courier\">USER_MANUAL_PT.pdf</font> - using the "
                "program, task by task.",
                "<font face=\"Courier\">TECHNICAL_MANUAL_PT.pdf</font> - how it "
                "works inside, and the command line.",
             ]),
             bullets([
                "<font face=\"Courier\">INSTALLATION_MANUAL_PT.pdf</font> - "
                "instala&ccedil;&atilde;o, em qualquer sistema.",
                "<font face=\"Courier\">USER_MANUAL_PT.pdf</font> - utilizar o "
                "programa, tarefa a tarefa.",
                "<font face=\"Courier\">TECHNICAL_MANUAL_PT.pdf</font> - como "
                "funciona por dentro, e a linha de comandos.",
             ])),
        pair(p("They are also on the <b>Ajuda</b> menu inside the program, "
               "which opens the Portuguese version when the interface is in "
               "Portuguese."),
             p("Est&atilde;o tamb&eacute;m no menu <b>Ajuda</b> dentro do "
               "programa, que abre a vers&atilde;o portuguesa quando a "
               "interface est&aacute; em portugu&ecirc;s.")))

    # --- 10. still stuck --------------------------------------------------
    s += step(
        10, "Still stuck?", "Ainda com dificuldades?",
        pair(p("Send a photograph or a screenshot of the <b>whole black "
               "window</b> - not just the error line. What was typed before it "
               "is usually what explains it. Add:"),
             p("Envie uma fotografia ou uma captura de <b>toda a janela "
               "preta</b> - n&atilde;o s&oacute; da linha do erro. O que foi "
               "escrito antes &eacute; normalmente o que explica tudo. "
               "Acrescente:")),
        pair(bullets([
                "the folder you extracted to;",
                "which step of this guide you had reached;",
                "whether <font face=\"Courier\">run.bat</font> worked or not.",
             ]),
             bullets([
                "a pasta para onde extraiu;",
                "em que passo deste guia estava;",
                "se o <font face=\"Courier\">run.bat</font> funcionou ou "
                "n&atilde;o.",
             ])),
        pair(note("Nothing you type in the Command Prompt can damage the "
                  "collection: <font face=\"Courier\">valves.db</font> is a "
                  "single file and you can always copy it somewhere safe first. "
                  "Experiment freely."),
             note("Nada do que escrever na Linha de Comandos pode estragar a "
                  "colec&ccedil;&atilde;o: <font face=\"Courier\">valves.db</font> "
                  "&eacute; um &uacute;nico ficheiro e pode sempre "
                  "copi&aacute;-lo antes para um s&iacute;tio seguro. "
                  "Experimente &agrave; vontade.")))

    # --- cheat sheet ------------------------------------------------------
    s.append(Spacer(1, 14))
    card = Table([[
        Paragraph(
            "<b>The whole thing, in three lines / Tudo, em tr&ecirc;s linhas</b>",
            S["conlabel"])], [
        Preformatted(
            "1.  Extract the zip to  C:\\valve-inventory\n"
            "    Extrair o zip para  C:\\valve-inventory\n"
            "\n"
            "2.  Double-click  run.bat        (duplo clique)\n"
            "\n"
            "3.  If that fails: Windows key -> cmd -> Enter, then\n"
            "    Se falhar: tecla Windows -> cmd -> Enter, depois\n"
            "        cd C:\\valve-inventory\n"
            "        python valves_gui.py",
            ParagraphStyle("card", parent=S["code"], fontSize=8.6, leading=11.5,
                           backColor=None, spaceAfter=0, spaceBefore=0))]],
        colWidths=[FRAME_W])
    card.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.9, INK),
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (0, 0), 8),
        ("BOTTOMPADDING", (0, 1), (0, 1), 9),
    ]))
    s.append(KeepTogether(card))

    s.append(Spacer(1, 10))
    s.append(pair(
        [Paragraph(
            "MIT-licensed and provided without warranty of any kind - see "
            "<font face=\"Courier\">LICENSE</font>. Hobbyist tooling for one "
            "attic, not a certified reference: treat every inferred parameter "
            "as a lead to check against a real datasheet, especially where "
            "lethal voltages are involved.", S["caption"])],
        [Paragraph(
            "Licenciado sob a licen&ccedil;a MIT e fornecido sem qualquer "
            "garantia - ver <font face=\"Courier\">LICENSE</font>. &Eacute; uma "
            "ferramenta amadora para um s&oacute;t&atilde;o, n&atilde;o uma "
            "refer&ecirc;ncia certificada: trate cada par&acirc;metro inferido "
            "como uma pista a confirmar numa folha de dados real, sobretudo "
            "onde h&aacute; tens&otilde;es letais.", S["caption"])]))
    return s


def main():
    doc = SimpleDocTemplate(
        os.path.join(HERE, OUT), pagesize=PAGE,
        leftMargin=LMARGIN, rightMargin=RMARGIN,
        topMargin=TMARGIN, bottomMargin=BMARGIN,
        title="Valve Inventory - Getting started on Windows (EN/PT)",
        author="Valve inventory toolkit")
    doc.build(story(), onFirstPage=decorate, onLaterPages=decorate)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
