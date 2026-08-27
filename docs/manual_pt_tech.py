#!/usr/bin/env python3
"""
manual_pt_tech.py - the Portuguese text of the Technical Manual.

Partial by design, and honestly so. What is translated here is everything a
reader needs to *navigate* the manual: the title and blurb, every section and
subsection heading, both reference tables (the file/role map and the full CLI
command list), and the short entries around them - 88 of its 142 strings.

What is not translated is the long internals prose: how migrate() decides
what to ALTER, why the Browse tab filters in Python rather than SQL, the
reasoning behind take_from_lot()'s deletion order. That material is aimed at
someone reading valvelib.py alongside it, is dense with identifiers that stay
in English anyway, and a rushed translation of it would be worse than none.
It falls back to English paragraph by paragraph, inside a fully Portuguese
structure, and `build_manuals.py --coverage` says exactly how much is left.

The User, Installation and Upgrade manuals - the three a collector actually
reads - are translated in full.
"""

PT_TECH = {
    "Technical Manual": "Manual Técnico",
    "Architecture, schema, and internals - for anyone extending the tool, scripting against "
    "the database directly, or just wanting to know how a feature actually works under the "
    "hood.":
        "Arquitectura, esquema e funcionamento interno - para quem queira estender a "
        "ferramenta, trabalhar directamente sobre a base de dados, ou simplesmente perceber "
        "como é que uma funcionalidade funciona por dentro.",

    # ---- section headings -------------------------------------------------
    "1. Architecture": "1. Arquitectura",
    "2. Database schema": "2. Esquema da base de dados",
    "3. Type-name normalisation and classification":
        "3. Normalização e classificação de nomes de tipo",
    "4. GUI internals worth knowing":
        "4. Detalhes internos da interface que vale a pena conhecer",
    "5. The research/import pipeline": "5. O processo de pesquisa e importação",
    "6. CLI command reference": "6. Referência de comandos da linha de comandos",
    "7. Version control and the snapshot design":
        "7. Controlo de versões e o desenho do retrato em texto",
    "8. Privacy note on distributing this data":
        "8. Nota de privacidade sobre a distribuição destes dados",
    "9. Extending the tool": "9. Estender a ferramenta",

    # ---- subsection headings ---------------------------------------------
    "valve_type - one row per type, the reference library":
        "valve_type - uma linha por tipo, a biblioteca de referência",
    "stock - one row per physical lot": "stock - uma linha por lote físico",
    "valve - one row per individually-tracked physical valve":
        "valve - uma linha por cada válvula física registada individualmente",
    "valve_test - one row per test of one valve, or of one section":
        "valve_test - uma linha por cada ensaio de uma válvula, ou de uma secção",
    "socket - one row per lot of bases/sockets":
        "socket - uma linha por lote de bases/suportes",
    "sundry / box": "sundry / box",
    "document - extra datasheets, links, and the general reference library":
        "document - folhas de dados adicionais, ligações e a biblioteca de referência geral",
    "v_stock (view)": "v_stock (vista)",
    "Keeping qty and the individual rows in step":
        "Manter a quantidade e as linhas individuais coerentes",
    "Migrations": "Migrações",
    "norm(name)": "norm(name)",
    "classify(name)": "classify(name)",
    "Equivalents-aware search": "Pesquisa que reconhece equivalentes",
    "Similar-types suggestions": "Sugestões de tipos semelhantes",
    "Browse tab - Category vs. Function":
        "Separador Explorar - Categoria versus Função",
    "Repair Bench - composition over duplication":
        "Bancada - composição em vez de duplicação",
    "Expected reply format": "Formato esperado da resposta",
    "Confirmed vs. lead-only": "Confirmado versus apenas indício",

    # ---- the file/role table ---------------------------------------------
    "File": "Ficheiro",
    "Role": "Função",
    "Schema (SCHEMA string, executed via executescript), type-name normalisation (norm()), "
    "and the naming-convention classifier (classify()).":
        "Esquema (a cadeia SCHEMA, executada por executescript), normalização de nomes de "
        "tipo (norm()) e o classificador de convenções de nomes (classify()).",
    "Command-line front end. One cmd_* function per subcommand, dispatched via argparse.":
        "Interface de linha de comandos. Uma função cmd_* por subcomando, despachada por "
        "argparse.",
    "Tkinter desktop front end. A single App(ttk.Frame) class holding four tabs' worth of "
    "widgets and handlers.":
        "Interface gráfica em Tkinter. Uma única classe App(ttk.Frame) que contém os "
        "componentes e tratadores de todos os separadores.",
    "One-off converter from the original 38-tab spreadsheet. Already run; kept for "
    "provenance, not part of normal operation.":
        "Conversor único a partir da folha de cálculo original de 38 separadores. Já foi "
        "executado; guardado como registo de proveniência, não faz parte do funcionamento "
        "normal.",
    "Writes/restores the data/ text snapshot that stands in for the binary database in "
    "version control.":
        "Escreve e restaura o retrato em texto em data/ que substitui a base de dados "
        "binária no controlo de versões.",
    "Two-stage, rate-limited crawler/downloader for the local datasheet archive "
    "(frank.pocnet.net only).":
        "Recolha e descarregamento em duas fases, com limite de ritmo, para o arquivo local "
        "de folhas de dados (apenas frank.pocnet.net).",
    "Parses a Claude research reply (block format below) and applies it to valve_type.":
        "Interpreta uma resposta de pesquisa do Claude (formato em blocos, abaixo) e "
        "aplica-a a valve_type.",
    "No framework - a flat script of check()/check_true() calls, exits non-zero on first "
    "failure.":
        "Sem framework - um programa simples com chamadas check()/check_true(), que termina "
        "com código diferente de zero à primeira falha.",

    # ---- CLI reference table ---------------------------------------------
    "Command": "Comando",
    "Purpose": "Para que serve",
    "List a box's contents.": "Lista o conteúdo de uma caixa.",
    "Which boxes hold a type (follows equivalents).":
        "Que caixas têm um tipo (segue os equivalentes).",
    "Full reference record for a type.": "Registo de referência completo de um tipo.",
    "Add stock; creates the type automatically if new, and reports the lot id it created.":
        "Adiciona existências; cria o tipo automaticamente se for novo, e indica o id do lote "
        "criado.",
    "Show a lot and the individual valves in it, with each one's latest test.":
        "Mostra um lote e as válvulas individuais que contém, com o último ensaio de cada "
        "uma.",
    "Track a lot's valves individually, one row per valve. Idempotent - only ever tops a lot "
    "up.":
        "Regista as válvulas de um lote individualmente, uma linha por válvula. Idempotente - "
        "apenas completa o lote.",
    "Show or edit one individual valve and its test history.":
        "Mostra ou edita uma válvula individual e o seu histórico de ensaios.",
    "Record one test. Every reading optional; always inserts, never overwrites.":
        "Regista um ensaio. Todas as leituras são opcionais; insere sempre, nunca substitui.",
    "That valve's full test history, newest first.":
        "O histórico completo de ensaios dessa válvula, do mais recente para o mais antigo.",
    "Lots whose individual rows and quantity disagree.":
        "Lotes em que as linhas individuais e a quantidade não coincidem.",
    "Remove stock you've used; individual rows go too, least documented first.":
        "Remove existências que gastou; as linhas individuais também saem, começando pelas "
        "menos documentadas.",
    "List valve base/socket stock.": "Lista as existências de bases/suportes de válvulas.",
    "Same idea as add/take/move, for bases/sockets.":
        "A mesma ideia de add/take/move, para bases/suportes.",
    "Edit a type's reference parameters; --confirm marks it confirmed.":
        "Edita os parâmetros de referência de um tipo; --confirm marca-o como confirmado.",
    "Candidate duplicate type pairs, for review before merge.":
        "Pares de tipos possivelmente duplicados, para rever antes de os juntar.",
    "Link local datasheet files into the database by filename.":
        "Associa à base de dados os ficheiros locais de folhas de dados pelo nome.",
    "Locate (and optionally open) a type's local datasheet.":
        "Localiza (e opcionalmente abre) a folha de dados local de um tipo.",
    "What still needs data, ordered by quantity held.":
        "O que ainda precisa de dados, ordenado pela quantidade que possui.",
    "Collection summary.": "Resumo da colecção.",
    "Write an .xlsx snapshot (requires openpyxl).":
        "Escreve um retrato em .xlsx (requer openpyxl).",
}
