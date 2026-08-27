#!/usr/bin/env python3
"""
manual_pt.py - the Portuguese text of the four manuals.

Keyed by the exact English string as it appears in build_manuals.py. The
lookup happens inside the eight layout helpers there (title/h1/h2/h3/p/note/
bullets/table), so nothing in the manual content itself had to be rearranged
to make it translatable, and anything missing here simply comes out in
English rather than breaking the build.

  python3 build_manuals.py --lang pt      builds the four *_PT.pdf
  python3 build_manuals.py --coverage     lists what is still in English

A key must match its English original character for character, reportlab
markup and typographic quotes included - which is why the practical way to
add one is to run --coverage and copy the string it prints.

Terminology follows Portuguese electronics usage: valvula for the valve
itself, anodo for the anode, grelha for a grid, filamento/aquecimento for the
heater, and folha de dados for a datasheet. Product and file names, shell
commands and code are left alone - "valves.db" is a filename in any language.
"""

PT = {

    # ======================================================================
    # Shared
    # ======================================================================
    "Valve Inventory": "Inventário de Válvulas",
    "Symptom": "Sintoma",
    "Likely cause / fix": "Causa provável / solução",

    # ======================================================================
    # INSTALLATION MANUAL
    # ======================================================================
    "Installation Manual": "Manual de Instalação",

    "This covers getting the tool running from nothing - whether you're setting it up "
    "for the first time, or you were handed an exported copy by someone else (see File "
    "&gt; Export archive and tools in the app, or QUICKSTART.md). <b>Already have an "
    "installation and moving to a newer version instead? See the Upgrade Guide, not this "
    "document</b> - the procedure for keeping your existing collection is different from "
    "a from-scratch setup.":
        "Isto explica como pôr a ferramenta a funcionar do zero - quer esteja a instalá-la "
        "pela primeira vez, quer lhe tenham dado uma cópia exportada por outra pessoa (ver "
        "Ficheiro &gt; Exportar arquivo e ferramentas na aplicação, ou o QUICKSTART.md). "
        "<b>Já tem uma instalação e quer apenas passar para uma versão mais recente? Consulte "
        "o Guia de Actualização e não este documento</b> - o procedimento para manter a "
        "colecção que já tem é diferente do de uma instalação de raiz.",

    "1. Requirements": "1. Requisitos",
    '<b>Python 3.8 or later.</b> Check with <font face="Courier">python3 --version</font>.':
        '<b>Python 3.8 ou posterior.</b> Verifique com '
        '<font face="Courier">python3 --version</font>.',
    '<b>tkinter</b>, for the desktop window. Ships with most Python installs; on '
    'Debian/Ubuntu it\'s a separate package: '
    '<font face="Courier">sudo apt install python3-tk</font>.':
        '<b>tkinter</b>, para a janela do ambiente de trabalho. Vem com a maioria das '
        'instalações de Python; no Debian/Ubuntu é um pacote à parte: '
        '<font face="Courier">sudo apt install python3-tk</font>.',
    '<b>openpyxl</b>, only if you want to export a spreadsheet snapshot: '
    '<font face="Courier">pip install openpyxl</font>.':
        '<b>openpyxl</b>, apenas se quiser exportar uma folha de cálculo: '
        '<font face="Courier">pip install openpyxl</font>.',
    '<b>reportlab</b>, only if you want to regenerate these manuals: '
    '<font face="Courier">pip install reportlab</font>.':
        '<b>reportlab</b>, apenas se quiser voltar a gerar estes manuais: '
        '<font face="Courier">pip install reportlab</font>.',
    "Nothing else is required at runtime. The database engine (SQLite) is built into "
    "Python's standard library - there is no server to install or configure.":
        "Não é preciso mais nada para o executar. O motor de base de dados (SQLite) faz "
        "parte da biblioteca padrão do Python - não há servidor nenhum para instalar ou "
        "configurar.",

    "2. Getting the files": "2. Obter os ficheiros",
    'The repository is <font face="Courier">GarethDaviesLondon/ValveInventory</font> on '
    'GitHub: <font face="Courier">https://github.com/GarethDaviesLondon/ValveInventory</font>. '
    'Three ways to get a working copy:':
        'O repositório é <font face="Courier">GarethDaviesLondon/ValveInventory</font> no '
        'GitHub: <font face="Courier">https://github.com/GarethDaviesLondon/ValveInventory'
        '</font>. Há três formas de obter uma cópia:',
    "2a. Clone the repository (latest)": "2a. Clonar o repositório (versão mais recente)",
    "Tracks ongoing development on the main branch.":
        "Acompanha o desenvolvimento em curso no ramo principal.",
    "2b. Download a tagged release (recommended once one exists)":
        "2b. Descarregar uma versão publicada (recomendado, quando existir)",
    "A tagged release is a known-good snapshot rather than whatever main happens to be at "
    "the moment - the first is planned as <b>v1.0</b>. Once it's out:":
        "Uma versão publicada é um retrato estável, e não aquilo em que o ramo principal "
        "calha estar no momento - a primeira está planeada como <b>v1.0</b>. Assim que "
        "sair:",
    '<b>No git needed</b> - open '
    '<font face="Courier">https://github.com/GarethDaviesLondon/ValveInventory/releases'
    '</font>, pick the release (e.g. v1.0), and download its “Source code (zip)” '
    'asset under Assets. Unzip it and follow section 3 below as normal.':
        '<b>Sem precisar de git</b> - abra '
        '<font face="Courier">https://github.com/GarethDaviesLondon/ValveInventory/releases'
        '</font>, escolha a versão (por exemplo v1.0) e descarregue o ficheiro '
        '“Source code (zip)” em Assets. Descompacte-o e siga a secção 3 abaixo '
        'normalmente.',
    "<b>With git</b> - clone just that tag rather than the full history:":
        "<b>Com git</b> - clone apenas essa etiqueta em vez do histórico completo:",
    "No release has been tagged yet at the time of writing - until v1.0 lands, use 2a "
    "(clone) or ask whoever gave you this manual for their own export (2c).":
        "À data em que isto é escrito ainda não foi publicada nenhuma versão - até sair a "
        "v1.0, use 2a (clonar) ou peça a quem lhe deu este manual a exportação dele (2c).",
    "2c. You were given an exported .zip": "2c. Deram-lhe um .zip exportado",
    "Produced by File &gt; Export archive and tools in the GUI. Just unzip it anywhere - "
    "it's not tied to git.":
        "Produzido por Ficheiro &gt; Exportar arquivo e ferramentas na interface gráfica. "
        "Basta descompactá-lo onde quiser - não depende do git.",

    "3. Building the database": "3. Construir a base de dados",
    'The working database, <font face="Courier">valves.db</font>, is never itself committed '
    'or exported - it\'s a binary SQLite file that would just bloat version control and '
    'can\'t be diffed. What travels with the project is a text snapshot in '
    '<font face="Courier">data/</font>, which rebuilds it:':
        'A base de dados de trabalho, <font face="Courier">valves.db</font>, nunca é ela '
        'própria guardada no controlo de versões nem exportada - é um ficheiro SQLite '
        'binário que só inchava o repositório e que não se pode comparar. O que viaja com o '
        'projecto é um retrato em texto em <font face="Courier">data/</font>, que a '
        'reconstrói:',
    'This reads <font face="Courier">data/valves.sql</font> and writes a fresh '
    '<font face="Courier">valves.db</font> next to it. Safe to re-run any time - it will '
    'refuse to overwrite an existing database unless you pass '
    '<font face="Courier">--force</font>.':
        'Isto lê o <font face="Courier">data/valves.sql</font> e escreve um '
        '<font face="Courier">valves.db</font> novo ao lado. Pode voltar a correr quando '
        'quiser - recusa-se a substituir uma base de dados existente a menos que indique '
        '<font face="Courier">--force</font>.',

    "4. Confirming it worked": "4. Confirmar que resultou",
    'This runs a fast set of checks - the type-name classifier, a database round-trip, each '
    'CLI command against a scratch copy, and (if <font face="Courier">data/</font> is '
    'present) the restore path itself. It should print '
    '<font face="Courier">all checks passed</font> and exit cleanly. If it doesn\'t, see '
    'Troubleshooting below before going further.':
        'Isto corre um conjunto rápido de verificações - o classificador de nomes de tipo, '
        'uma ida e volta à base de dados, cada comando da linha de comandos contra uma cópia '
        'temporária e (se existir <font face="Courier">data/</font>) o próprio caminho de '
        'restauro. Deve escrever <font face="Courier">all checks passed</font> e terminar sem '
        'erros. Se não o fizer, consulte a Resolução de problemas abaixo antes de continuar.',

    "5. Running it": "5. Executar",
    "Desktop window": "Janela do ambiente de trabalho",
    "Command line": "Linha de comandos",
    'Both read and write the same <font face="Courier">valves.db</font> - there is no '
    'separate setup for one versus the other.':
        'Ambas lêem e escrevem o mesmo <font face="Courier">valves.db</font> - não há '
        'configuração separada para uma ou para a outra.',

    "6. The datasheet archive (optional)":
        "6. O arquivo de folhas de dados (opcional)",
    "PDF datasheets are not included in a clone or an export - hundreds of megabytes of "
    "third-party files that would swamp the repository. Build your own copy locally:":
        "As folhas de dados em PDF não vão incluídas num clone nem numa exportação - são "
        "centenas de megabytes de ficheiros de terceiros que afogariam o repositório. "
        "Construa a sua própria cópia localmente:",
    "The default 2-second delay between requests is deliberate - the source site runs on "
    "donations. Both stages are resumable, so Ctrl-C is always safe. If you'd rather have "
    "Claude do this work (including finding sources beyond that one site), the GUI's Tools "
    "&gt; Generate datasheet download prompt... writes a ready-to-use prompt for an agent "
    "with file and web access, such as Claude Code.":
        "O atraso predefinido de 2 segundos entre pedidos é intencional - o sítio de origem "
        "vive de donativos. As duas fases podem ser retomadas, por isso Ctrl-C é sempre "
        "seguro. Se preferir que seja o Claude a fazer este trabalho (incluindo procurar "
        "fontes para além desse sítio), Ferramentas &gt; Gerar instruções para descarregar "
        "folhas de dados... escreve um texto pronto a usar para um agente com acesso a "
        "ficheiros e à web, como o Claude Code.",

    "7. Troubleshooting": "7. Resolução de problemas",
    "“No module named tkinter”": "“No module named tkinter”",
    "Install the platform tkinter package (e.g. python3-tk on Debian/Ubuntu); it isn't "
    "installable via pip.":
        "Instale o pacote tkinter do sistema (por exemplo python3-tk no Debian/Ubuntu); não "
        "se instala pelo pip.",
    "UnicodeDecodeError / UnicodeEncodeError during restore or CLI output":
        "UnicodeDecodeError / UnicodeEncodeError durante o restauro ou nas mensagens da "
        "linha de comandos",
    'Windows consoles default to a non-UTF-8 codepage; some collection notes contain '
    'Cyrillic and other non-Latin text. This tool\'s own scripts already force UTF-8 - if '
    'you hit this in a modified copy, add encoding="utf-8" to the relevant open() call and '
    'sys.stdout.reconfigure(encoding="utf-8") near the top of main().':
        'As consolas do Windows usam por omissão uma codificação que não é UTF-8; algumas '
        'notas da colecção contêm cirílico e outros caracteres não latinos. Os programas '
        'desta ferramenta já forçam UTF-8 - se isto lhe acontecer numa cópia modificada, '
        'acrescente encoding="utf-8" à chamada open() em causa e '
        'sys.stdout.reconfigure(encoding="utf-8") no início de main().',
    "“valves.db already exists” on restore":
        "“valves.db already exists” ao restaurar",
    "Expected safety behaviour - pass --force if you intend to overwrite it, or "
    "delete/rename the existing file first if you're not sure what's in it.":
        "É a protecção a funcionar - indique --force se tenciona substituí-lo, ou apague/"
        "mude o nome do ficheiro existente primeiro se não tiver a certeza do que lá está.",
    "GUI window closes immediately, no error visible":
        "A janela fecha-se imediatamente, sem erro visível",
    "Run python3 valves_gui.py from a terminal instead of double-clicking the file, so any "
    "traceback stays visible after the window closes.":
        "Execute python3 valves_gui.py a partir de um terminal em vez de clicar duas vezes "
        "no ficheiro, para que a mensagem de erro fique visível depois de a janela fechar.",
    "openpyxl / reportlab import errors": "Erros ao importar openpyxl / reportlab",
    "Both are optional - only needed for File > Export spreadsheet and for rebuilding these "
    "manuals respectively. pip install the missing one, or simply avoid that feature.":
        "Ambos são opcionais - só são precisos para Ficheiro > Exportar folha de cálculo e "
        "para voltar a gerar estes manuais, respectivamente. Instale o que faltar com pip, "
        "ou simplesmente não use essa funcionalidade.",

    "8. Starting your own collection": "8. Começar a sua própria colecção",
    "The database that ships in this repository is the author's own stock - real box "
    "locations in a real attic, not sample data. To make it yours instead:":
        "A base de dados que vem neste repositório é o stock do próprio autor - localizações "
        "reais de caixas num sótão real, e não dados de exemplo. Para a tornar sua:",
    "Option A - start empty": "Opção A - começar do zero",
    "Delete the working database and launch the app; a fresh, empty one is created "
    "automatically the moment anything tries to open it:":
        "Apague a base de dados de trabalho e abra a aplicação; é criada automaticamente uma "
        "nova, vazia, assim que alguma coisa tente abri-la:",
    "Option B - keep the reference library, clear the stock":
        "Opção B - manter a biblioteca de referência e limpar as existências",
    "The researched valve types (function, base, heater, ratings) are useful on their own "
    "regardless of whose valves they are - keep that, wipe out the boxes and quantities "
    "that belong to the original owner's collection:":
        "Os tipos de válvula já pesquisados (função, base, aquecimento, valores máximos) são "
        "úteis por si só, sejam de quem forem as válvulas - guarde isso e apague as caixas e "
        "quantidades que pertencem à colecção do dono original:",
    'Either way, run <font face="Courier">python3 snapshot.py</font> afterward if you want '
    'your own fork\'s <font face="Courier">data/</font> to reflect the change before '
    'committing.':
        'Em qualquer dos casos, corra a seguir <font face="Courier">python3 snapshot.py'
        '</font> se quiser que a pasta <font face="Courier">data/</font> do seu repositório '
        'reflicta a alteração antes de a guardar no controlo de versões.',

    "9. License and disclaimer": "9. Licença e exoneração de responsabilidade",
    'MIT-licensed - see the <font face="Courier">LICENSE</font> file included in this '
    'repository. MIT is about as permissive as licenses get; its one real obligation, '
    'keeping the copyright notice attached, is also what gives it attribution. The data in '
    '<font face="Courier">data/</font> carries its own, separate note in '
    '<font face="Courier">LICENSE</font> - some of the descriptive text there is third-party '
    'material gathered from reference sites, not the author\'s to relicense.':
        'Licenciado sob a licença MIT - ver o ficheiro <font face="Courier">LICENSE</font> '
        'incluído neste repositório. A MIT é das licenças mais permissivas que há; a sua '
        'única obrigação real, manter o aviso de direitos de autor, é também o que lhe dá a '
        'atribuição. Os dados em <font face="Courier">data/</font> têm uma nota própria e '
        'separada no <font face="Courier">LICENSE</font> - parte do texto descritivo é '
        'material de terceiros recolhido em sítios de referência, que não é do autor para '
        'relicenciar.',
    'This software is provided without warranty of any kind, express or implied, and you use '
    'it entirely at your own risk. It is hobbyist tooling built for one person\'s attic, not '
    'a certified reference - treat every “inferred” parameter as a lead to verify '
    'against a real datasheet, not a settled fact, especially before relying on it for '
    'anything involving the lethal voltages a valve amplifier runs at. By downloading, '
    'installing, or running this application, you are confirming that you have reviewed the '
    'source for yourself and that you accept these terms.':
        'Este programa é fornecido sem qualquer garantia, expressa ou implícita, e utiliza-o '
        'inteiramente por sua conta e risco. É uma ferramenta amadora feita para o sótão de '
        'uma pessoa, e não uma referência certificada - trate cada parâmetro '
        '“deduzido” como uma pista a confirmar numa folha de dados verdadeira e '
        'não como um facto assente, sobretudo antes de confiar nele para seja o que for que '
        'envolva as tensões letais a que funciona um amplificador a válvulas. Ao '
        'descarregar, instalar ou executar esta aplicação, está a confirmar que reviu o '
        'código por si próprio e que aceita estas condições.',

    # ======================================================================
    # UPGRADE GUIDE
    # ======================================================================
    "Upgrade Guide": "Guia de Actualização",
    "How to move from an older installed version to a newer one - say, v1.3 to v1.4 - "
    "without losing anything you've added. This is a living document: the general procedure "
    "below applies to every release so far and is expected to keep applying, but check "
    "“Version-specific notes” at the end for anything a particular release calls "
    "out as different.":
        "Como passar de uma versão instalada mais antiga para uma mais recente - por "
        "exemplo, da v1.3 para a v1.4 - sem perder nada do que acrescentou. Este documento "
        "vai sendo actualizado: o procedimento geral abaixo aplica-se a todas as versões até "
        "hoje e espera-se que continue a aplicar-se, mas veja as “Notas por versão” "
        "no fim para o caso de alguma versão indicar algo diferente.",
    "The short answer": "A resposta curta",
    '<b>No, it isn\'t export-and-reimport.</b> All of your data - stock, box locations, '
    'confirmed parameters, everything - lives in one file, '
    '<font face="Courier">valves.db</font>, and upgrading never touches that file directly. '
    'Back it up (below), get the new version\'s code, and run it against your existing '
    'database. That\'s the whole procedure.':
        '<b>Não, não é exportar e voltar a importar.</b> Todos os seus dados - existências, '
        'localizações das caixas, parâmetros confirmados, tudo - vivem num único ficheiro, o '
        '<font face="Courier">valves.db</font>, e actualizar nunca lhe toca directamente. '
        'Faça uma cópia de segurança (abaixo), obtenha o código da versão nova e execute-o '
        'sobre a base de dados que já tem. É todo o procedimento.',
    'This works because every schema change so far has been strictly additive - new tables '
    'and new columns only, never a renamed or removed one. The app brings its schema up to '
    'date against your existing database on every single startup '
    '(<font face="Courier">V.init_db()</font>): it creates whatever tables are new '
    '(<font face="Courier">CREATE TABLE IF NOT EXISTS</font>) and adds whatever columns are '
    'new (<font face="Courier">ALTER TABLE ... ADD COLUMN</font>, from v1.4 on). On an '
    'up-to-date database that\'s a no-op; on an older one it happens in place, leaving every '
    'value already there untouched - SQLite\'s ADD COLUMN appends a nullable column to the '
    'table definition without rewriting any existing row.':
        'Isto funciona porque todas as alterações ao esquema feitas até hoje foram '
        'estritamente aditivas - apenas tabelas e colunas novas, nunca uma renomeada ou '
        'removida. A aplicação põe o esquema em dia sobre a base de dados existente em cada '
        'arranque (<font face="Courier">V.init_db()</font>): cria as tabelas que sejam novas '
        '(<font face="Courier">CREATE TABLE IF NOT EXISTS</font>) e acrescenta as colunas que '
        'sejam novas (<font face="Courier">ALTER TABLE ... ADD COLUMN</font>, a partir da '
        'v1.4). Numa base de dados já actualizada não faz nada; numa mais antiga faz tudo no '
        'próprio ficheiro, deixando intacto todo o valor que já lá estava - o ADD COLUMN do '
        'SQLite acrescenta uma coluna anulável à definição da tabela sem reescrever nenhuma '
        'linha existente.',
    "1. Back up first - always": "1. Faça primeiro uma cópia de segurança - sempre",
    "Do this before touching anything else. Two options, and it's fine to do both:":
        "Faça isto antes de mexer em mais alguma coisa. Há duas opções, e pode fazer as "
        "duas:",
    "Copy the file (fastest, most robust)":
        "Copiar o ficheiro (mais rápido e mais seguro)",
    'Copy <font face="Courier">valves.db</font> itself to somewhere safe - another folder, a '
    'dated backup folder, cloud storage, a USB stick. If you\'ve built a local datasheet '
    'archive, copy the <font face="Courier">datasheets/</font> folder too (optional - it\'s '
    'rebuildable, just slower to redo than to copy).':
        'Copie o próprio <font face="Courier">valves.db</font> para um sítio seguro - outra '
        'pasta, uma pasta de cópias com data, armazenamento na nuvem, uma pen USB. Se tiver '
        'construído um arquivo local de folhas de dados, copie também a pasta '
        '<font face="Courier">datasheets/</font> (opcional - dá para reconstruir, só demora '
        'mais a refazer do que a copiar).',
    "Refresh the text snapshot": "Actualizar o retrato em texto",
    'Writes a human-readable copy into <font face="Courier">data/</font> - good to have '
    'regardless, and if you track your own fork in git, commit it so you have real version '
    'history of your collection, not just a single backup snapshot.':
        'Escreve uma cópia legível em <font face="Courier">data/</font> - vale sempre a pena, '
        'e se acompanhar o seu próprio repositório em git, guarde-a no controlo de versões '
        'para ter um verdadeiro histórico da colecção e não apenas uma cópia isolada.',
    "2. Get the new version": "2. Obter a versão nova",
    "If you're on a git clone": "Se estiver num clone git",
    '<font face="Courier">valves.db</font> is gitignored, so neither command touches it - '
    'only the code and docs update. Nothing further to do for the database itself.':
        'O <font face="Courier">valves.db</font> está fora do controlo de versões, por isso '
        'nenhum dos comandos lhe toca - só o código e a documentação são actualizados. Não é '
        'preciso fazer mais nada quanto à base de dados.',
    "If you're using a downloaded copy (no git)":
        "Se estiver a usar uma cópia descarregada (sem git)",
    'Download the new release and extract it to a <b>new</b> folder - don\'t extract over '
    'the old one. Then copy your existing <font face="Courier">valves.db</font> (and '
    '<font face="Courier">datasheets/</font>, if you have one, and anything under '
    '<font face="Courier">docs/screenshots/</font> you added yourself) from the old folder '
    'into the new one.':
        'Descarregue a versão nova e extraia-a para uma pasta <b>nova</b> - não extraia por '
        'cima da antiga. Depois copie o seu <font face="Courier">valves.db</font> (e a pasta '
        '<font face="Courier">datasheets/</font>, se tiver, e tudo o que tenha acrescentado '
        'em <font face="Courier">docs/screenshots/</font>) da pasta antiga para a nova.',
    "3. Run it": "3. Executar",
    "First launch against the upgraded code creates any new tables the new version needs, "
    "against your existing data, automatically. You should see your full collection "
    "immediately - same counts, same boxes, same confirmed parameters.":
        "O primeiro arranque com o código actualizado cria automaticamente, sobre os seus "
        "dados existentes, as tabelas novas de que a versão precise. Deve ver de imediato a "
        "colecção completa - as mesmas contagens, as mesmas caixas, os mesmos parâmetros "
        "confirmados.",
    "4. Confirm nothing's missing": "4. Confirmar que não falta nada",
    'Then Tools &gt; Collection summary (or '
    '<font face="Courier">python3 valves.py stats</font>) and check the totals match what '
    'you expect. If anything looks off, your backup from step 1 is right there.':
        'Depois Ferramentas &gt; Resumo da colecção (ou '
        '<font face="Courier">python3 valves.py stats</font>) e confirme que os totais são os '
        'que esperava. Se alguma coisa parecer errada, a cópia de segurança do passo 1 está '
        'ali mesmo.',
    'Optionally, refresh the snapshot again now that you\'re upgraded, so '
    '<font face="Courier">data/</font> reflects the current version\'s schema too:':
        'Se quiser, actualize outra vez o retrato agora que já está na versão nova, para que '
        '<font face="Courier">data/</font> reflicta também o esquema actual:',
    "What not to do": "O que não fazer",
    'Don\'t run <font face="Courier">snapshot.py --restore</font> as part of upgrading. That '
    'rebuilds <font face="Courier">valves.db</font> FROM the last-committed '
    '<font face="Courier">data/valves.sql</font> - which discards anything you\'ve added to '
    'your live database since the last time you ran plain '
    '<font face="Courier">snapshot.py</font>. It\'s the right tool for a fresh clone that '
    'has no database yet at all (see the Installation Manual), not for upgrading one you '
    'already have.':
        'Não corra <font face="Courier">snapshot.py --restore</font> como parte da '
        'actualização. Isso reconstrói o <font face="Courier">valves.db</font> A PARTIR do '
        'último <font face="Courier">data/valves.sql</font> guardado - o que deita fora tudo '
        'o que tenha acrescentado à base de dados desde a última vez que correu o '
        '<font face="Courier">snapshot.py</font> simples. É a ferramenta certa para um clone '
        'novo que ainda não tem base de dados nenhuma (ver o Manual de Instalação), e não '
        'para actualizar uma que já tem.',
    "Version-specific notes": "Notas por versão",
    "Nothing beyond the standard procedure above has ever been required. Entries below "
    "record what each release actually changed about the database, and are worth a read "
    "before upgrading - but if there's nothing here for the version you're moving to, the "
    "standard procedure is all you need.":
        "Nunca foi necessário nada para além do procedimento normal acima. As entradas "
        "abaixo registam o que cada versão alterou de facto na base de dados, e vale a pena "
        "lê-las antes de actualizar - mas se não houver aqui nada sobre a versão para onde "
        "vai, o procedimento normal é tudo o que precisa.",
    "v1.5": "v1.5",
    "No schema change at all - this release is interface only, so the standard procedure "
    "covers it and your database is untouched. It adds a Portuguese translation of the whole "
    "interface and of the manuals, switched with the two flags at the top right of the "
    "window; a tested/untested filter on the Valves and Browse tabs; a Notes column on the "
    "individual-valves list; and a double-click route from a Browse result's box breakdown "
    "straight into that lot's individual valves.":
        "Nenhuma alteração ao esquema - esta versão só mexe na interface, por isso o "
        "procedimento normal chega e a base de dados fica intacta. Acrescenta uma tradução "
        "para português de toda a interface e dos manuais, que se troca com as duas bandeiras "
        "no canto superior direito da janela; um filtro ensaiada/por ensaiar nos separadores "
        "Válvulas e Explorar; uma coluna Notas na lista de válvulas individuais; e um caminho "
        "directo, com duplo clique, da distribuição por caixas de um resultado do separador "
        "Explorar para as válvulas individuais desse lote.",
    'The interface language is remembered in a file called '
    '<font face="Courier">.lang</font> beside the database. It holds nothing but the chosen '
    'language, is per-machine rather than part of the collection, and is not '
    'version-controlled - delete it and the app simply opens in English.':
        'O idioma da interface fica guardado num ficheiro chamado '
        '<font face="Courier">.lang</font> junto da base de dados. Não contém mais nada além '
        'do idioma escolhido, é próprio de cada computador e não faz parte da colecção, e '
        'não vai para o controlo de versões - apague-o e a aplicação abre simplesmente em '
        'inglês.',
    "v1.4": "v1.4",
    "v1.3": "v1.3",
    "v1.1 - v1.2": "v1.1 - v1.2",
    'Adds one new table (<font face="Courier">document</font> - extra datasheets, links, and '
    'the general reference library) and a Docs tab. Purely additive, created automatically '
    'on first run - no manual steps.':
        'Acrescenta uma tabela nova (<font face="Courier">document</font> - folhas de dados '
        'adicionais, ligações e a biblioteca de referência geral) e um separador Documentos. '
        'Puramente aditivo, criado automaticamente no primeiro arranque - sem passos '
        'manuais.',
    'v1.1 added an auto-restore prompt for a brand-new database with no '
    '<font face="Courier">valves.db</font> yet; irrelevant if you\'re upgrading an existing '
    'one. No schema changes. (There was no separate v1.2 release.)':
        'A v1.1 acrescentou um pedido de restauro automático para uma base de dados nova sem '
        '<font face="Courier">valves.db</font>; irrelevante se estiver a actualizar uma que '
        'já existe. Sem alterações ao esquema. (Não houve uma versão v1.2 separada.)',
}

# The User Manual is the longest of the four and the one most likely to be
# edited, so its text lives in its own module and is merged in here.
from manual_pt_user import PT_USER          # noqa: E402
from manual_pt_tech import PT_TECH          # noqa: E402
PT.update(PT_USER)
PT.update(PT_TECH)
