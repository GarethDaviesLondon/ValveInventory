#!/usr/bin/env python3
"""
manual_pt_user.py - the Portuguese text of the User Manual.

Split out of manual_pt.py, which merges it, purely for size: the User Manual
is the longest of the four and the one most likely to be edited. Same rules
apply - keys must match the English original character for character, and
--coverage is the way to get one right.
"""

PT_USER = {
    "User Manual": "Manual do Utilizador",
    "A task-by-task walkthrough of the desktop application. For the command-line "
    "equivalent of anything here, see the Technical Manual's command reference, or "
    "README.md.":
        "Um percurso tarefa a tarefa pela aplicação gráfica. Para o equivalente na linha de "
        "comandos de qualquer coisa aqui descrita, ver a lista de comandos do Manual Técnico "
        "ou o README.md.",

    # ---- overview ---------------------------------------------------------
    "Overview": "Visão geral",
    "The window opens on five tabs, described below, sharing one database. Nothing you do "
    "in one tab is hidden from the others - move stock in the Valves tab and the Browse "
    "tab's counts update the next time you search it.":
        "A janela abre com cinco separadores, descritos abaixo, sobre a mesma base de dados. "
        "Nada do que faz num separador fica escondido dos outros - mova existências no "
        "separador Válvulas e as contagens do separador Explorar são actualizadas da próxima "
        "vez que lá pesquisar.",
    "<b>Valves</b> - search, edit reference data, add/take/move/delete stock.":
        "<b>Válvulas</b> - pesquisar, editar dados de referência, adicionar/retirar/mover/"
        "eliminar existências.",
    "<b>Bases / Sockets</b> - the same idea, for the sockets themselves rather than the "
    "valves that plug into them.":
        "<b>Bases / Suportes</b> - a mesma ideia, para os próprios suportes e não para as "
        "válvulas que neles encaixam.",
    "<b>Browse</b> - a parametric filter across every held type, for “what do I have "
    "that could work here” questions.":
        "<b>Explorar</b> - um filtro por parâmetros sobre todos os tipos que possui, para "
        "perguntas do género “o que é que eu tenho que possa servir aqui”.",
    "<b>Repair Bench</b> - for “I've got this valve out of a set I'm fixing - what is "
    "it, and what have I got that could stand in for it?”":
        "<b>Bancada</b> - para “tirei esta válvula de um aparelho que estou a arranjar "
        "- o que é, e o que tenho que a possa substituir?”",
    "<b>Docs</b> - a general reference library for material that isn't about one specific "
    "type - care-and-feeding guides, base wiring references, and the like.":
        "<b>Documentos</b> - uma biblioteca de referência geral para material que não é sobre "
        "um tipo específico - guias de utilização, esquemas de ligação de bases e afins.",

    # ---- language ---------------------------------------------------------
    "English or Portuguese": "Inglês ou português",
    "Two flags sit at the top right of the window. Click either to put the whole interface "
    "into that language - menus, tab names, buttons, column headings, filter captions, "
    "dialogs, the About box and the user guide all change together. The choice is remembered "
    "for next time, and switching costs nothing: no window is rebuilt, so your filters, the "
    "selected box and any open popup stay exactly as they were.":
        "Há duas bandeiras no canto superior direito da janela. Clique numa delas para pôr "
        "toda a interface nesse idioma - menus, nomes dos separadores, botões, cabeçalhos das "
        "colunas, legendas dos filtros, caixas de diálogo, a janela Acerca e o guia do "
        "utilizador mudam todos ao mesmo tempo. A escolha fica guardada para a próxima vez, e "
        "trocar não custa nada: nenhuma janela é reconstruída, por isso os seus filtros, a "
        "caixa seleccionada e qualquer janela aberta ficam exactamente como estavam.",
    "What does <i>not</i> change is the collection. Type designations, box names, makers, "
    "origins and your own notes stay exactly as they were typed - a valve is an EL84 in any "
    "language, and a bag labelled “Saco Pingo Doce” is called that because that is "
    "what is written on it. The filter dropdowns are filled from the database, so their "
    "contents stay in the language of the data too. Only the tool's own wording moves.":
        "O que <i>não</i> muda é a colecção. As designações dos tipos, os nomes das caixas, "
        "as marcas, as origens e as suas próprias notas ficam exactamente como as escreveu - "
        "uma válvula é uma EL84 em qualquer idioma, e um saco identificado como “Saco "
        "Pingo Doce” chama-se assim porque é isso que lá está escrito. As listas de "
        "filtros são preenchidas a partir da base de dados, por isso o seu conteúdo também "
        "fica no idioma dos dados. Só muda o texto da própria ferramenta.",

    # ---- valves tab -------------------------------------------------------
    "The Valves tab": "O separador Válvulas",
    "Boxes sidebar": "Barra lateral das caixas",
    "Click a box to filter the results to it; click “All boxes” to clear. Click a "
    "column heading (Box / Types / Qty) to sort, click again to reverse.":
        "Clique numa caixa para limitar os resultados a ela; clique em “All "
        "boxes” para limpar. Clique num cabeçalho de coluna (Caixa / Tipos / Qtd) para "
        "ordenar, e outra vez para inverter.",
    "Search row": "Linha de pesquisa",
    'Text, Function, Base, and the numeric fields (Heater V, Pa W, Freq MHz), which accept '
    'comparisons like <font face="Courier">&gt;20</font>, <font face="Courier">&lt;7</font>, '
    '<font face="Courier">&gt;=250</font> as well as an exact value.':
        'Texto, Função, Base e os campos numéricos (Aquecimento V, Pa W, Freq MHz), que '
        'aceitam comparações como <font face="Courier">&gt;20</font>, '
        '<font face="Courier">&lt;7</font>, <font face="Courier">&gt;=250</font> além de um '
        'valor exacto.',
    "Searching a type by name also pulls in stock of anything cross-referenced as its "
    "equivalent - search ECF80 and PCF80 stock shows up too, in blue, labelled which type "
    "it's equivalent to. This is a hint toward substitutes, not a claim they're necessarily "
    "interchangeable in every circuit.":
        "Procurar um tipo pelo nome traz também as existências de tudo o que esteja "
        "registado como seu equivalente - procure ECF80 e as existências de PCF80 também "
        "aparecem, a azul, indicando de que tipo são equivalentes. Isto é uma pista para "
        "substituições e não uma afirmação de que são forçosamente permutáveis em qualquer "
        "circuito.",
    "<b>Advanced...</b> opens a dialog covering every remaining field - manufacturer, "
    "condition, family, gm, mu, power out, confidence, and whether a datasheet is linked. It "
    "edits the same underlying filters as the quick row, so the two stay in sync.":
        "<b>Avançado...</b> abre uma janela com todos os restantes campos - fabricante, "
        "estado, família, gm, mu, potência de saída, confiança, e se tem folha de dados "
        "associada. Edita os mesmos filtros que a linha rápida, por isso as duas mantêm-se "
        "coerentes.",
    "Results table": "Tabela de resultados",
    "Click a heading to sort. Double-click a row to open its datasheet. <b>Amber</b> rows "
    "have unconfirmed (inferred) parameters; <b>blue</b> rows are equivalents pulled in by a "
    "search.":
        "Clique num cabeçalho para ordenar. Clique duas vezes numa linha para abrir a folha "
        "de dados. As linhas a <b>âmbar</b> têm parâmetros não confirmados (deduzidos); as "
        "linhas a <b>azul</b> são equivalentes trazidos por uma pesquisa.",
    "Detail panel": "Painel de detalhe",
    "The selected row's type record, editable in place. <b>Save</b> keeps it inferred; "
    "<b>Save + confirm</b> marks it confirmed and the row turns from amber to black - that "
    "transition is the progress bar for working through the collection.":
        "O registo de tipo da linha seleccionada, editável ali mesmo. <b>Guardar</b> "
        "mantém-no como deduzido; <b>Guardar + confirmar</b> marca-o como confirmado e a "
        "linha passa de âmbar a preto - essa passagem é a barra de progresso de quem está a "
        "percorrer a colecção.",
    "Below the fields, <b>Similar types</b> lists other held types with the same broad "
    "function and every shared electrical rating within 50% - candidates for a substitute "
    "with modification, not verified equivalents. Heater mismatches are flagged, not "
    "filtered out, since a dropping resistor or a different supply can often cover that. "
    "Double-click a suggestion to look it up.":
        "Por baixo dos campos, <b>Tipos semelhantes</b> lista outros tipos que possui com a "
        "mesma função geral e todos os valores eléctricos comuns dentro de 50% - candidatos "
        "a substituição com alterações, e não equivalentes confirmados. As diferenças de "
        "aquecimento são assinaladas e não escondidas, porque muitas vezes uma resistência "
        "em série ou outra alimentação resolvem. Clique duas vezes numa sugestão para a "
        "consultar.",
    "<b>Open datasheet</b> opens the local PDF if there is one, otherwise falls back to an "
    "online source - the button itself reads <i>Open datasheet (local)</i> or <i>Find "
    "datasheet (web)</i>, so which one it'll do is clear before you click. <b>RadioMuseum</b> "
    "and <b>Web search</b> run a site-scoped or general search for whatever's selected. "
    "<b>Manage...</b> (<b>Manage information...</b> on the Browse tab's popup) opens the full "
    "document list for a type: the one “primary” sheet that button opens, plus as "
    "many extra datasheets and links as you like - a second manufacturer's sheet, a forum "
    "thread, a project that happens to use this valve. Upload a file you already have, or "
    "paste a URL (no download needed for a link - it's just recorded). Its <b>Edit "
    "parameters...</b> button opens the same field-entry form as the detail panel, so a "
    "Browse-tab research session never needs to switch tabs to record what a datasheet says.":
        "<b>Abrir folha de dados</b> abre o PDF local se existir; caso contrário recorre a "
        "uma fonte em linha - o próprio botão diz <i>Abrir folha de dados (local)</i> ou "
        "<i>Procurar folha de dados (web)</i>, por isso sabe-se o que vai acontecer antes de "
        "clicar. <b>RadioMuseum</b> e <b>Pesquisar na web</b> fazem uma pesquisa limitada a "
        "esse sítio ou geral sobre o que estiver seleccionado. <b>Gerir...</b> (<b>Gerir "
        "informação...</b> na janela do separador Explorar) abre a lista completa de "
        "documentos de um tipo: a folha “principal” que aquele botão abre, mais "
        "tantas folhas e ligações adicionais quantas quiser - a folha de outro fabricante, um "
        "tópico de fórum, um projecto que use esta válvula. Carregue um ficheiro que já "
        "tenha, ou cole um URL (para uma ligação não é preciso descarregar nada - fica apenas "
        "registada). O botão <b>Editar parâmetros...</b> abre o mesmo formulário do painel de "
        "detalhe, para que uma sessão de pesquisa no separador Explorar nunca tenha de mudar "
        "de separador para registar o que a folha de dados diz.",
    "Toolbar": "Barra de ferramentas",
    "<b>Add stock</b> creates the type automatically if it's new, classifying it from its "
    "designation. <b>Edit lot</b>, <b>Individual valves...</b>, <b>Take</b>, <b>Move</b>, and "
    "<b>Delete lot</b> act on the selected row. <b>Move</b> also offers a position in the "
    "destination box; leaving it blank clears the old one, which belonged to the box the lot "
    "has just left.":
        "<b>Adicionar existências</b> cria o tipo automaticamente se for novo, "
        "classificando-o a partir da designação. <b>Editar lote</b>, <b>Válvulas "
        "individuais...</b>, <b>Retirar</b>, <b>Mover</b> e <b>Eliminar lote</b> actuam sobre "
        "a linha seleccionada. <b>Mover</b> permite também indicar uma posição na caixa de "
        "destino; deixando em branco apaga a antiga, que pertencia à caixa de onde o lote "
        "acabou de sair.",
    "The two editors either side of the results table do different jobs. <b>Edit lot</b> "
    "changes this one physical lot - where it is, what it came from, how it tested. The panel "
    "on the right changes the reference record shared by <i>every</i> lot of that type.":
        "Os dois editores de cada lado da tabela de resultados fazem coisas diferentes. "
        "<b>Editar lote</b> altera este lote físico - onde está, de onde veio, como se "
        "comportou no ensaio. O painel da direita altera o registo de referência partilhado "
        "por <i>todos</i> os lotes desse tipo.",

    # ---- what a lot records ----------------------------------------------
    "What a lot records": "O que um lote regista",
    "A lot is one physical batch: this many of this type, in this box. Two Mullard EL84s out "
    "of different sets are one <i>type</i> but two <i>lots</i>, and it's the lot that knows "
    "which shelf it sits on and which set it came out of. Beyond quantity, manufacturer and "
    "condition, each lot can record:":
        "Um lote é um conjunto físico: esta quantidade deste tipo, nesta caixa. Duas EL84 "
        "Mullard vindas de aparelhos diferentes são um <i>tipo</i> mas dois <i>lotes</i>, e é "
        "o lote que sabe em que prateleira está e de que aparelho saiu. Para além da "
        "quantidade, fabricante e estado, cada lote pode registar:",
    "Field": "Campo",
    "What goes in it": "O que lá vai",
    "Position": "Posição",
    "Where in the box it sits, as a grid reference - B-12, row and column.":
        "Onde está dentro da caixa, como uma referência de grelha - B-12, linha e coluna.",
    "Type 1 / Type 2": "Tipo 1 / Tipo 2",
    "Other designations the valve is marked with: a US number, a service code, a second "
    "maker's part number.":
        "Outras designações marcadas na válvula: um número americano, um código militar, a "
        "referência de outro fabricante.",
    "Origin": "Origem",
    "Where it came from - bought, inherited, or the set it came out of.":
        "De onde veio - comprada, herdada, ou o aparelho de onde saiu.",
    "Test values": "Valores de ensaio",
    "What it measured on a tester.": "O que mediu num aparelho de ensaio.",
    "Other": "Outros",
    "Anything else: boxed or unboxed, odd printing, whatever the row needs.":
        "Tudo o resto: com ou sem caixa, impressão invulgar, o que a linha precisar.",
    '<b>Every one of them is optional</b>, and blank is a perfectly normal value - none of '
    'them changes how anything else behaves. Fill them in from <b>Add stock</b>, from '
    '<b>Edit lot</b> afterwards, from the upload CSV, or from the command line with '
    '<font face="Courier">valves.py add</font> / <font face="Courier">valves.py edit</font>.':
        '<b>Todos eles são opcionais</b>, e em branco é um valor perfeitamente normal - '
        'nenhum deles altera o comportamento de mais nada. Preencha-os em <b>Adicionar '
        'existências</b>, depois em <b>Editar lote</b>, no CSV de importação, ou na linha de '
        'comandos com <font face="Courier">valves.py add</font> / '
        '<font face="Courier">valves.py edit</font>.',
    "Type 1 and Type 2 sit on the lot rather than the type on purpose: they record what "
    "<i>this</i> glass is actually marked with, which is not always the designation you file "
    "it under. They're searchable either way, so a valve stored as EL84 and printed 6BQ5 is "
    "found by either name. That's separate from the type record's <i>equivalents</i> list, "
    "which is a claim about the types themselves rather than about one batch's printing.":
        "O Tipo 1 e o Tipo 2 pertencem ao lote e não ao tipo de propósito: registam o que "
        "<i>este</i> vidro tem realmente escrito, que nem sempre é a designação sob a qual o "
        "arquivou. São pesquisáveis de qualquer das formas, por isso uma válvula guardada "
        "como EL84 e impressa 6BQ5 encontra-se por qualquer dos nomes. Isso é coisa distinta "
        "da lista de <i>equivalentes</i> do registo de tipo, que é uma afirmação sobre os "
        "próprios tipos e não sobre a impressão de um lote em concreto.",
    "Position is a plain grid reference rather than two separate row and column fields, so "
    "it fits whatever scheme a box already uses - B-12, 3/4, or a shelf name. Lot listings "
    "sort by it, with un-positioned lots last, so a partly-positioned box still reads top to "
    "bottom.":
        "A Posição é uma simples referência de grelha e não dois campos separados de linha e "
        "coluna, para se adaptar ao esquema que cada caixa já use - B-12, 3/4, ou o nome de "
        "uma prateleira. As listagens de lotes ordenam por ela, com os lotes sem posição no "
        "fim, para que uma caixa parcialmente posicionada continue a ler-se de cima para "
        "baixo.",
    'On the command line, a listing leaves out any of these columns that\'s empty for every '
    'row it\'s showing, so <font face="Courier">valves.py box 12</font> looks exactly as it '
    'always did until there\'s something in there to show. In the window they\'re '
    'always-present columns on the results table, since the table scrolls sideways and a '
    'stable column layout is easier to work against.':
        'Na linha de comandos, uma listagem omite qualquer destas colunas que esteja vazia em '
        'todas as linhas mostradas, por isso <font face="Courier">valves.py box 12</font> '
        'aparece exactamente como sempre apareceu até haver ali alguma coisa para mostrar. Na '
        'janela são colunas sempre presentes na tabela de resultados, porque a tabela desliza '
        'na horizontal e é mais fácil trabalhar com um conjunto de colunas estável.',

    # ---- individual valves ------------------------------------------------
    "Individual valves and testing": "Válvulas individuais e ensaios",
    "A lot is a quantity - “6 x KT66 in box 8” - and for most of a collection that "
    "is all it ever needs to be. Where it isn't, select the lot and click <b>Individual "
    "valves...</b>, then <b>Track individually</b>. That creates one row per valve held, and "
    "from then on each valve is a thing in its own right: its own position on the shelf, its "
    "own serial or date code, its own maker and condition where a lot is mixed, and its own "
    "test history.":
        "Um lote é uma quantidade - “6 x KT66 na caixa 8” - e para a maior parte "
        "de uma colecção nunca precisa de ser mais do que isso. Quando precisa, seleccione o "
        "lote e clique em <b>Válvulas individuais...</b> e depois em <b>Registar "
        "individualmente</b>. Isso cria uma linha por cada válvula existente, e a partir daí "
        "cada válvula passa a ser uma coisa por direito próprio: a sua posição na prateleira, "
        "o seu número de série ou código de data, a sua marca e estado quando o lote é misto, "
        "e o seu histórico de ensaios.",
    "Expanding a lot is opt-in and per lot, so a box of a hundred identical indicators stays "
    "one line until you decide otherwise. It is also safe to repeat - it only ever tops a lot "
    "up to the quantity it holds, never duplicates or resets what is already there. The "
    "<b>Ind</b> column on the results table shows how many of each lot are tracked this way; "
    "blank means the lot is still just a quantity. New lots added with <b>Add stock</b> are "
    "tracked individually from the start unless the form says otherwise.":
        "Expandir um lote é opcional e feito lote a lote, por isso uma caixa com cem "
        "indicadores iguais continua a ser uma linha até decidir o contrário. Também é seguro "
        "repetir - só completa o lote até à quantidade que ele tem, nunca duplica nem repõe o "
        "que já lá está. A coluna <b>Ind</b> na tabela de resultados mostra quantas válvulas "
        "de cada lote estão registadas assim; em branco significa que o lote ainda é apenas "
        "uma quantidade. Os lotes novos criados com <b>Adicionar existências</b> ficam "
        "registados individualmente desde o início, salvo indicação em contrário no "
        "formulário.",
    "The <b>Notes</b> column in that list is what was written about that one valve - a serial "
    "read off the glass, “no box”, “another one at home”. It belongs to "
    "the valve rather than the lot, which is the whole point of tracking individually: a "
    "remark that applies to one valve out of six says nothing useful once it has been pooled "
    "onto all six.":
        "A coluna <b>Notas</b> nessa lista é o que foi escrito sobre aquela válvula em "
        "concreto - um número de série lido no vidro, “sem caixa”, “outra "
        "em casa”. Pertence à válvula e não ao lote, que é precisamente a razão de as "
        "registar individualmente: um comentário que se aplica a uma válvula em seis deixa de "
        "dizer o que quer que seja de útil depois de ser atribuído às seis.",

    # ---- recording a test -------------------------------------------------
    "Recording a test": "Registar um ensaio",
    "<b>Record test...</b> logs one test of the selected valve. Every reading is optional, "
    "because no single tester produces all of them: an emission tester gives one figure, an "
    "AVO VCM163 reads anode current and mutual conductance on two meters at once plus "
    "separate gas and insulation tests, a curve tracer gives everything. A record holding "
    "nothing but a gm figure and a date is a perfectly good record.":
        "<b>Registar um ensaio</b> regista um ensaio da válvula seleccionada. Todas as "
        "leituras são opcionais, porque nenhum aparelho de ensaio as produz todas: um "
        "medidor de emissão dá um único valor, um AVO VCM163 lê a corrente de ânodo e a "
        "condutância mútua em dois mostradores ao mesmo tempo, mais ensaios separados de gás "
        "e isolamento, e um traçador de curvas dá tudo. Um registo com apenas um valor de gm "
        "e uma data é um registo perfeitamente válido.",
    "Units": "Unidades",
    "What it is": "O que é",
    "Tested on, Tester": "Data do ensaio, Aparelho",
    "When, and on what. A test dated 1901-01-01 is one recovered from a written record that "
    "gave no date - nothing was tested in 1901, the valve had not been invented, so the date "
    "reads unmistakably as “tested, date unknown” rather than as a real "
    "measurement day.":
        "Quando, e em quê. Um ensaio com a data 1901-01-01 é um ensaio recuperado de um "
        "registo escrito que não indicava a data - nada foi ensaiado em 1901, a válvula ainda "
        "não tinha sido inventada, por isso a data lê-se inequivocamente como "
        "“ensaiada, data desconhecida” e não como um dia de medição real.",
    "Va, Vg at test": "Va, Vg no ensaio",
    "V": "V",
    "The conditions the readings were taken under. A gm figure means nothing without them.":
        "As condições em que as leituras foram feitas. Um valor de gm não significa nada sem "
        "elas.",
    "Bias mode": "Tipo de polarização",
    "Fixed or auto. The same valve reads differently under each.":
        "Fixa ou automática. A mesma válvula lê valores diferentes em cada uma.",
    "Ia": "Ia",
    "mA": "mA",
    "Anode (plate) current - the headline figure on most testers, and what power valves are "
    "matched on.":
        "Corrente de ânodo - o valor principal na maioria dos aparelhos, e aquele pelo qual "
        "as válvulas de potência são emparelhadas.",
    "Ig2": "Ig2",
    "Screen current, for tetrodes and pentodes.":
        "Corrente de grelha ecrã, para tétrodos e pêntodos.",
    "gm": "gm",
    "mA/V": "mA/V",
    "Mutual conductance. British practice throughout; multiply by 1000 for the micromhos an "
    "American tester shows.":
        "Condutância mútua. Usa-se a prática britânica; multiplique por 1000 para os "
        "micromhos que um aparelho americano mostra.",
    "gm as % of nominal": "gm em % do nominal",
    "%": "%",
    "How valves are actually graded and sold.":
        "É assim que as válvulas são de facto classificadas e vendidas.",
    "Emission": "Emissão",
    "The single reading a cheap emission tester gives.":
        "A leitura única que um medidor de emissão barato dá.",
    "Gas / grid current": "Corrente de gás / grelha",
    "uA": "uA",
    "The gas test - an AVO reads to 100 uA full scale.":
        "O ensaio de gás - um AVO lê até 100 uA de fundo de escala.",
    "Insulation": "Isolamento",
    "Mohm": "Mohm",
    "Interelectrode leakage.": "Fugas entre eléctrodos.",
    "Heater-cathode": "Filamento-cátodo",
    "The separate cathode/heater test: a figure, or pass/fail.":
        "O ensaio separado cátodo/filamento: um valor, ou passa/não passa.",
    "Shorts, Verdict": "Curto-circuitos, Veredicto",
    "Pass/fail, and your overall call on the valve.":
        "Passa/não passa, e a sua avaliação global da válvula.",
    "Testing is never destructive. Each test is a new row, so retesting a valve years later "
    "builds its history rather than replacing it - and the trend between two readings is "
    "usually the interesting part. <b>Test history...</b>, or a double-click on the valve, "
    "shows every test of it, newest first.":
        "Ensaiar nunca destrói nada. Cada ensaio é uma linha nova, por isso voltar a ensaiar "
        "uma válvula anos depois acrescenta ao histórico em vez de o substituir - e a "
        "evolução entre duas leituras é normalmente a parte interessante. <b>Histórico de "
        "ensaios</b>, ou um duplo clique na válvula, mostra todos os ensaios dela, do mais "
        "recente para o mais antigo.",
    "The tester and the test conditions are carried forward from that valve's last test, "
    "since they rarely change across a session and the readings always do.":
        "O aparelho e as condições de ensaio são reaproveitados do último ensaio dessa "
        "válvula, porque raramente mudam ao longo de uma sessão e as leituras mudam sempre.",
    "Double triodes": "Duplos tríodos",
    "A double triode is recorded a section at a time: run <b>Record test</b> twice, once with "
    "Section <i>a</i> and once with <i>b</i>. That is how the readings come off the meter, "
    "and comparing the two sections is the whole point of testing an ECC83 for phase-inverter "
    "duty. The valve list shows the most recent test of either section; the history shows "
    "both.":
        "Um duplo tríodo regista-se uma secção de cada vez: faça <b>Registar um ensaio</b> "
        "duas vezes, uma com a Secção <i>a</i> e outra com a <i>b</i>. É assim que as "
        "leituras saem do aparelho, e comparar as duas secções é precisamente o objectivo de "
        "ensaiar uma ECC83 para funcionar como inversora de fase. A lista de válvulas mostra "
        "o ensaio mais recente de qualquer das secções; o histórico mostra os dois.",
    "Colours in the valve list": "Cores na lista de válvulas",
    "<b>Amber</b> rows are valves that have never been tested. <b>Red-brown</b> rows are ones "
    "whose last verdict was weak, short or failed.":
        "As linhas a <b>âmbar</b> são válvulas nunca ensaiadas. As linhas a "
        "<b>castanho-avermelhado</b> são aquelas cujo último veredicto foi fraca, "
        "curto-circuito ou avariada.",
    "Using valves up, and correcting the record":
        "Gastar válvulas, e corrigir o registo",
    "These are two different things and they behave differently. <b>Take</b>, on the Valves "
    "tab, is for a valve you have actually used: it reduces the lot's quantity and removes "
    "that many individual rows as well, choosing the <i>least documented</i> first - untested "
    "before tested, unmarked before serial-numbered - so using valves up never quietly "
    "discards test history you took the trouble to record. <b>Remove valve</b>, in the "
    "dialog, is for a row that should not have been there: it deletes the record and leaves "
    "the quantity alone.":
        "São duas coisas diferentes e comportam-se de maneira diferente. <b>Retirar</b>, no "
        "separador Válvulas, é para uma válvula que gastou mesmo: reduz a quantidade do lote "
        "e remove também esse número de linhas individuais, escolhendo primeiro as <i>menos "
        "documentadas</i> - por ensaiar antes das ensaiadas, sem marcação antes das que têm "
        "número de série - para que gastar válvulas nunca deite fora, sem avisar, histórico "
        "de ensaios que teve o trabalho de registar. <b>Remover válvula</b>, na caixa de "
        "diálogo, é para uma linha que não devia lá estar: apaga o registo e não mexe na "
        "quantidade.",
    "Deleting a valve takes its test history with it, and deleting a lot takes its valves and "
    "their tests. That is deliberate - a test belongs to a particular piece of glass and "
    "means nothing without it - but it is the one irreversible action here, so the dialog "
    "says what will go before it goes.":
        "Apagar uma válvula leva com ela o seu histórico de ensaios, e apagar um lote leva as "
        "suas válvulas e os ensaios delas. Isto é intencional - um ensaio pertence a um "
        "determinado vidro e não significa nada sem ele - mas é a única acção irreversível "
        "aqui, por isso a caixa de diálogo diz o que vai desaparecer antes de desaparecer.",
    "<b>Tools &gt; Check individual valve counts</b> reports any lot where the quantity and "
    "the number of individual rows have drifted apart. It reports rather than corrects: which "
    "of the two is right depends on what is actually in the box.":
        "<b>Ferramentas &gt; Verificar contagem de válvulas individuais</b> indica qualquer "
        "lote em que a quantidade e o número de linhas individuais tenham deixado de "
        "coincidir. Comunica em vez de corrigir: qual das duas está certa depende do que "
        "está realmente dentro da caixa.",

    # ---- other tabs -------------------------------------------------------
    "The Bases / Sockets tab": "O separador Bases / Suportes",
    "Valve bases and sockets aren't valves, so they're tracked in their own table rather than "
    "mixed into the general sundry catch-all. Same pattern as the Valves tab: search by base "
    "type or box, Add / Take / Move / Delete lot.":
        "As bases e suportes de válvulas não são válvulas, por isso são registados numa "
        "tabela própria em vez de misturados com os diversos gerais. O mesmo padrão do "
        "separador Válvulas: pesquisar por tipo de base ou por caixa, e Adicionar / Retirar / "
        "Mover / Eliminar lote.",
    "The Browse tab": "O separador Explorar",
    "A faceted filter across all held types, closer to a shopping-site filter panel than a "
    "search box.":
        "Um filtro por facetas sobre todos os tipos que possui, mais parecido com o painel de "
        "filtros de uma loja em linha do que com uma caixa de pesquisa.",
    "<b>Category, Base, Family, Confidence, Variable-mu, Tested</b> - dropdowns that "
    "<i>cascade</i>: picking one narrows what the others still offer, so you never land on an "
    "empty combination. Category is a coarser bucket than the raw function text (Triode, "
    "Double triode, Tetrode, Pentode, Triode-pentode, Rectifier, and so on) - specifically so "
    "it's useful as a filter instead of nearly matching one type each.":
        "<b>Categoria, Base, Família, Confiança, Mu variável, Ensaiada</b> - listas que "
        "<i>encadeiam</i>: escolher uma estreita o que as outras ainda oferecem, por isso "
        "nunca se cai numa combinação vazia. A Categoria é um agrupamento mais grosseiro do "
        "que o texto da função (Tríodo, Duplo tríodo, Tétrodo, Pêntodo, Tríodo-pêntodo, "
        "Rectificador, e assim por diante) - precisamente para ser útil como filtro em vez de "
        "corresponder quase a um tipo cada.",
    "<b>Numeric ratings</b> (Heater V/A, Va max, Pa max, gm, mu, Power out, Freq max) - an "
    "operator (&lt; = &gt; &lt;= &gt;=) plus a value picked from what's actually present in "
    "the data.":
        "<b>Valores numéricos</b> (Aquecimento V/A, Va máx, Pa máx, gm, mu, Potência de "
        "saída, Freq máx) - um operador (&lt; = &gt; &lt;= &gt;=) mais um valor escolhido de "
        "entre os que existem de facto nos dados.",
    "<b>Name contains</b> - narrows the list as you type, e.g. “3cx” or "
    "“PL”.":
        "<b>Nome contém</b> - estreita a lista enquanto escreve, por exemplo "
        "“3cx” ou “PL”.",
    "Click a heading to sort. <b>Double-click a type</b> for a popup showing its full "
    "reference record, datasheet/web-search buttons, and a box-by-box breakdown of exactly "
    "where and how many you hold.":
        "Clique num cabeçalho para ordenar. <b>Clique duas vezes num tipo</b> para uma janela "
        "com o registo de referência completo, botões de folha de dados e pesquisa na web, e "
        "a distribuição caixa a caixa de onde estão e quantas tem.",
    "In that popup, <b>double-click one of the box rows</b> to drop straight into the "
    "individual valves of that lot. It is the same window the Valves tab reaches through "
    "<b>Individual valves...</b>, so a valve found by browsing behaves exactly like one found "
    "by searching - you can read its notes, see its test history and record a new test "
    "without going back to the Valves tab.":
        "Nessa janela, <b>clique duas vezes numa das linhas de caixa</b> para ir directamente "
        "às válvulas individuais desse lote. É a mesma janela a que o separador Válvulas "
        "chega por <b>Válvulas individuais...</b>, por isso uma válvula encontrada a explorar "
        "comporta-se exactamente como uma encontrada a pesquisar - pode ler as notas dela, "
        "ver o histórico de ensaios e registar um ensaio novo sem voltar ao separador "
        "Válvulas.",
    "The <b>Tested</b> facet narrows the list to types that hold at least one tested valve, "
    "or to those that hold none, and the <b>Tested</b> column counts them. The Valves tab "
    "carries the same filter for lots, beside its numeric fields, with a <b>Tstd</b> column "
    "next to <b>Ind</b>. Both count a lot or a type as tested when at least one valve in it "
    "has at least one recorded test; a lot with no individual valve rows at all therefore "
    "reads as untested, because nothing in it has been tested.":
        "O filtro <b>Ensaiada</b> restringe a lista aos tipos que têm pelo menos uma válvula "
        "ensaiada, ou àqueles que não têm nenhuma, e a coluna <b>Ensaiada</b> conta-as. O "
        "separador Válvulas tem o mesmo filtro para lotes, ao lado dos campos numéricos, com "
        "uma coluna <b>Ens</b> a seguir a <b>Ind</b>. Ambos consideram um lote ou um tipo "
        "como ensaiado quando pelo menos uma válvula dele tem pelo menos um ensaio "
        "registado; um lote sem nenhuma linha de válvula individual lê-se portanto como por "
        "ensaiar, porque nada nele foi ensaiado.",

    "The Repair Bench tab": "O separador Bancada",
    "The workflow for a valve pulled out of a set on the bench: type its designation (and, "
    "optionally, which circuit stage it came from - IF amp, audio output, rectifier, and so "
    "on), then <b>Identify</b>.":
        "O procedimento para uma válvula tirada de um aparelho na bancada: escreva a "
        "designação (e, se quiser, de que andar do circuito veio - amplificador de FI, saída "
        "de áudio, rectificador, e assim por diante) e depois <b>Identificar</b>.",
    "If it's already in your database": "Se já estiver na sua base de dados",
    "Its reference data loads straight into the form on the left. On the right, <b>In stock "
    "now</b> shows anything you already hold of that exact type or a listed equivalent, and "
    "<b>Possible substitutes</b> lists other held types with the same broad function and "
    "every shared rating within 50% - the same candidate logic as the Valves tab's Similar "
    "types, but scoped to what's actually in stock, and with a held-quantity count. "
    "Double-click a substitute to switch the whole bench over to it, if that turns out to be "
    "the more interesting question.":
        "Os dados de referência carregam directamente no formulário da esquerda. À direita, "
        "<b>Em stock agora</b> mostra o que já tem desse tipo exacto ou de um equivalente "
        "registado, e <b>Substitutos possíveis</b> lista outros tipos que possui com a mesma "
        "função geral e todos os valores comuns dentro de 50% - a mesma lógica dos Tipos "
        "semelhantes do separador Válvulas, mas limitada ao que existe realmente em stock e "
        "com a quantidade que tem. Clique duas vezes num substituto para passar toda a "
        "bancada para ele, se essa acabar por ser a pergunta mais interessante.",
    "If it's new to you": "Se for nova para si",
    "<b>Open datasheet</b>, <b>RadioMuseum</b>, and <b>Web search</b> work immediately off "
    "the typed designation, before anything is saved. <b>Copy research prompt</b> puts a "
    "ready-to-paste prompt on the clipboard, scoped to just this one type (a faster, "
    "single-item cousin of Tools &gt; Generate research prompt...) - paste it into Claude, "
    "and it comes back in the same block format Apply researched data... expects.":
        "<b>Abrir folha de dados</b>, <b>RadioMuseum</b> e <b>Pesquisar na web</b> funcionam "
        "logo a partir da designação escrita, antes de se guardar seja o que for. <b>Copiar "
        "instruções</b> coloca na área de transferência um texto pronto a colar, limitado a "
        "este único tipo (uma versão mais rápida e para um só item de Ferramentas &gt; Gerar "
        "instruções de pesquisa...) - cole-o no Claude, e a resposta vem no mesmo formato em "
        "blocos que Aplicar dados pesquisados... espera.",
    "<b>Add to database</b> creates a bare reference record (classified from the designation, "
    "no stock attached) so there's somewhere to save findings as you gather them. <b>Save</b> "
    "/ <b>Save + confirm</b> work exactly as in the Valves tab detail panel - and immediately "
    "refresh the substitute list on the right using whatever you just entered, so you can see "
    "straight away whether the parameters you found open up any new candidates from stock.":
        "<b>Adicionar à base de dados</b> cria um registo de referência vazio (classificado a "
        "partir da designação, sem existências associadas) para ter onde guardar o que for "
        "descobrindo. <b>Guardar</b> / <b>Guardar + confirmar</b> funcionam exactamente como "
        "no painel de detalhe do separador Válvulas - e actualizam de imediato a lista de "
        "substitutos à direita com o que acabou de introduzir, para ver logo se os parâmetros "
        "que encontrou abrem novos candidatos entre as suas existências.",

    "The Docs tab": "O separador Documentos",
    "A general reference library, for material that isn't about one specific valve type - a "
    "care-and-feeding guide for power tubes, a base wiring reference, anything worth keeping "
    "alongside the collection. <b>Add from file...</b> copies a PDF you already have into the "
    "local archive; <b>Add from URL...</b> just records a link, no download. Each entry gets "
    "a title and an optional abstract - select one to read its abstract in the pane on the "
    "right, and use the filter box to narrow the list as you type.":
        "Uma biblioteca de referência geral, para material que não é sobre um tipo de válvula "
        "específico - um guia de utilização de válvulas de potência, uma referência de "
        "ligações de bases, tudo o que valha a pena guardar junto da colecção. <b>Adicionar "
        "de ficheiro...</b> copia para o arquivo local um PDF que já tenha; <b>Adicionar de "
        "URL...</b> apenas regista uma ligação, sem descarregar nada. Cada entrada tem um "
        "título e um resumo opcional - seleccione uma para ler o resumo no painel da direita, "
        "e use a caixa de filtro para estreitar a lista enquanto escreve.",
    "The same title/abstract/file-or-URL idea also applies per type, via the Valves tab's or "
    "Repair Bench's <b>Manage...</b> button - the difference is only whether a document is "
    "filed against one valve type or kept in the general library.":
        "A mesma ideia de título/resumo/ficheiro-ou-URL aplica-se também por tipo, através do "
        "botão <b>Gerir...</b> do separador Válvulas ou da Bancada - a diferença está apenas "
        "em o documento ficar associado a um tipo de válvula ou guardado na biblioteca geral.",

    # ---- reference data, bulk, backup ------------------------------------
    "Filling in reference data": "Preencher os dados de referência",
    "New types start out with only what the naming convention can infer - a real datasheet "
    "reading is what actually confirms them. Three ways to close that gap:":
        "Os tipos novos começam apenas com o que a convenção de nomes permite deduzir - só a "
        "leitura de uma folha de dados verdadeira os confirma. Há três formas de fechar essa "
        "lacuna:",
    "By hand": "À mão",
    "Edit the fields in the detail panel and Save + confirm, as above.":
        "Editar os campos no painel de detalhe e Guardar + confirmar, como acima.",
    "With Claude - electrical parameters": "Com o Claude - parâmetros eléctricos",
    "Tools &gt; Generate research prompt... writes a prompt (for your highest-quantity "
    "unconfirmed types) to a text file. Paste it into any Claude chat, save the reply, then "
    "Tools &gt; Apply researched data.... Only what Claude actually confirmed is applied - a "
    "hedged finding (“could not verify”, “plausible”) is kept as a "
    "lead rather than marked confirmed, so nothing gets overclaimed.":
        "Ferramentas &gt; Gerar instruções de pesquisa... escreve num ficheiro de texto um "
        "pedido (para os seus tipos não confirmados com maior quantidade). Cole-o em qualquer "
        "conversa com o Claude, guarde a resposta, e depois Ferramentas &gt; Aplicar dados "
        "pesquisados.... Só é aplicado o que o Claude confirmou de facto - uma conclusão com "
        "reservas (“não foi possível verificar”, “plausível”) fica "
        "guardada como pista em vez de marcada como confirmada, para não se afirmar mais do "
        "que se sabe.",
    "With Claude - datasheet files": "Com o Claude - ficheiros de folhas de dados",
    "Tools &gt; Generate datasheet download prompt... writes a prompt aimed at an agent with "
    "file and web access (Claude Code, not a plain chat, since it needs to write files to "
    "your disk). It tries the built-in fetcher first, then searches further for whatever's "
    "still missing, and saves PDFs directly into the local archive.":
        "Ferramentas &gt; Gerar instruções para descarregar folhas de dados... escreve um "
        "pedido dirigido a um agente com acesso a ficheiros e à web (Claude Code, e não uma "
        "conversa simples, porque precisa de escrever ficheiros no seu disco). Tenta primeiro "
        "o descarregador incorporado, depois procura mais para o que ainda faltar, e guarda "
        "os PDF directamente no arquivo local.",

    "Adding stock in bulk": "Adicionar existências em lote",
    "For more than a few lots at once, skip the Add-stock dialog:":
        "Para mais do que uns poucos lotes de uma vez, dispense a janela de adicionar:",
    "<b>Tools &gt; Create upload template...</b> writes a blank CSV with the right columns, "
    "ready to fill in.":
        "<b>Ferramentas &gt; Criar modelo de importação...</b> escreve um CSV em branco com "
        "as colunas certas, pronto a preencher.",
    "<b>Tools &gt; Import upload CSV...</b> reads a filled-in CSV back in - one row per lot, "
    "new types classified automatically, existing types just get more stock.":
        "<b>Ferramentas &gt; Importar CSV...</b> lê de volta um CSV preenchido - uma linha "
        "por lote, os tipos novos classificados automaticamente, e os tipos existentes apenas "
        "recebem mais existências.",
    "<b>Tools &gt; Generate CSV-building prompt...</b> writes a prompt for any Claude chat "
    "that interviews you (or reads whatever spreadsheet, notes, or photos you describe) and "
    "hands back a ready-to-import CSV - useful when your existing records aren't already in "
    "this shape.":
        "<b>Ferramentas &gt; Gerar instruções para construir CSV...</b> escreve um pedido "
        "para qualquer conversa com o Claude, que lhe faz perguntas (ou lê a folha de "
        "cálculo, apontamentos ou fotografias que lhe descrever) e devolve um CSV pronto a "
        "importar - útil quando os registos que já tem não estão neste formato.",

    "Backup, export, and sharing": "Cópias de segurança, exportação e partilha",
    "Backup": "Cópia de segurança",
    "The database itself isn't the backup - the text snapshot is. Refresh it before ending a "
    "session of changes:":
        "A base de dados não é a cópia de segurança - o retrato em texto é. Actualize-o antes "
        "de terminar uma sessão de alterações:",
    "That's what belongs in version control; it's what a restore rebuilds from.":
        "É isso que pertence ao controlo de versões; é a partir daí que um restauro "
        "reconstrói tudo.",
    "Export a spreadsheet": "Exportar uma folha de cálculo",
    "File &gt; Export spreadsheet... writes a plain .xlsx for anyone who just wants to look, "
    "not use the tool.":
        "Ficheiro &gt; Exportar folha de cálculo... escreve um .xlsx simples para quem só "
        "quer ver, sem usar a ferramenta.",
    "Hand the whole thing to someone else": "Entregar tudo a outra pessoa",
    "File &gt; Export archive and tools (.zip)... bundles the code, docs, and a fresh "
    "snapshot into one file, with an option to strip the third-party descriptive text first "
    "(see the Technical Manual's note on that). The recipient unzips it and follows "
    "QUICKSTART.md, which is included.":
        "Ficheiro &gt; Exportar arquivo e ferramentas (.zip)... junta o código, a documentação "
        "e um retrato novo num único ficheiro, com a opção de retirar antes o texto "
        "descritivo de terceiros (ver a nota do Manual Técnico sobre isso). Quem o receber "
        "descompacta-o e segue o QUICKSTART.md, que vai incluído.",
}


# The last four Upgrade Guide paragraphs - the v1.4 release notes, which are
# long enough to sit here beside the User Manual rather than crowd manual_pt.py.
PT_USER.update({
    'Adds six optional columns to the <font face="Courier">stock</font> table - position, '
    'type1, type2, origin, test_values and other - so a lot can record where in its box it '
    'sits, what else the valve is marked as, and where it came from. This is the first '
    'release to add columns to an existing table rather than whole new tables, so it is the '
    'first to run an <font face="Courier">ALTER TABLE</font> against your database. It still '
    'needs no manual steps: first launch adds the columns in place and leaves every existing '
    'value untouched, and the new columns start out empty on every lot you already have. '
    'Fill them in as and when it\'s worth it - blank is a perfectly normal value, and '
    'nothing else in the tool changes behaviour because of them.':
        'Acrescenta seis colunas opcionais à tabela <font face="Courier">stock</font> - '
        'position, type1, type2, origin, test_values e other - para que um lote possa '
        'registar onde está dentro da caixa, que outras designações a válvula tem marcadas e '
        'de onde veio. Esta é a primeira versão a acrescentar colunas a uma tabela existente '
        'em vez de tabelas inteiramente novas, por isso é a primeira a correr um '
        '<font face="Courier">ALTER TABLE</font> sobre a sua base de dados. Continua a não '
        'exigir passos manuais: o primeiro arranque acrescenta as colunas no próprio ficheiro '
        'e deixa intacto todo o valor existente, e as colunas novas começam vazias em todos '
        'os lotes que já tem. Preencha-as quando valer a pena - vazio é um valor '
        'perfeitamente normal, e mais nada na ferramenta muda de comportamento por causa '
        'delas.',

    'It also adds two new tables, <font face="Courier">valve</font> (one row per '
    'individually-tracked physical valve) and <font face="Courier">valve_test</font> (one row '
    'per test of one), created automatically on first run like any other new table. Nothing '
    'about your existing collection changes when they appear: every lot stays exactly as it '
    'was, held as a quantity, until you expand one. See “Individual valves and '
    'testing” in the User Manual.':
        'Acrescenta também duas tabelas novas, <font face="Courier">valve</font> (uma linha '
        'por cada válvula física registada individualmente) e '
        '<font face="Courier">valve_test</font> (uma linha por cada ensaio de uma delas), '
        'criadas automaticamente no primeiro arranque como qualquer outra tabela nova. Nada '
        'muda na colecção que já tem quando elas aparecem: cada lote fica exactamente como '
        'estava, guardado como uma quantidade, até expandir algum. Ver “Válvulas '
        'individuais e ensaios” no Manual do Utilizador.',

    'One behaviour change worth knowing about even if you never expand a lot. <b>Take</b> now '
    'removes individual valve records alongside the quantity, and deleting a lot removes its '
    'valves and their tests. On a collection with nothing expanded there is nothing to remove '
    'and Take behaves exactly as before - but once you have recorded tests, a Take is the one '
    'thing that can discard them. It picks the least documented valves first precisely to '
    'make that unlikely.':
        'Há uma mudança de comportamento que vale a pena conhecer mesmo que nunca expanda um '
        'lote. <b>Retirar</b> passa a remover registos de válvulas individuais juntamente com '
        'a quantidade, e apagar um lote remove as suas válvulas e os ensaios delas. Numa '
        'colecção sem nada expandido não há nada para remover e Retirar comporta-se '
        'exactamente como antes - mas assim que tiver ensaios registados, um Retirar é a '
        'única coisa que os pode deitar fora. Escolhe primeiro as válvulas menos documentadas '
        'precisamente para tornar isso improvável.',

    'Two things worth knowing if you script against the database yourself. The '
    '<font face="Courier">v_stock</font> view is dropped and recreated on that first launch - '
    'it gains position, the alternative designations, origin and an '
    '<font face="Courier">individuals</font> count - so any view of your own built <i>on top '
    'of</i> v_stock should be checked afterwards. And <font face="Courier">data/stock.csv'
    '</font> gains six columns (plus two new files, <font face="Courier">valves.csv</font> '
    'and <font face="Courier">tests.csv</font>), so the first '
    '<font face="Courier">snapshot.py</font> run after upgrading will show a large diff for '
    'that file even if you\'ve changed nothing - that\'s the header and the new empty fields, '
    'not lost data.':
        'Duas coisas que vale a pena saber se escrever os seus próprios programas contra a '
        'base de dados. A vista <font face="Courier">v_stock</font> é apagada e recriada '
        'nesse primeiro arranque - ganha a posição, as designações alternativas, a origem e '
        'uma contagem <font face="Courier">individuals</font> - por isso qualquer vista sua '
        'construída <i>por cima</i> de v_stock deve ser verificada a seguir. E o '
        '<font face="Courier">data/stock.csv</font> ganha seis colunas (mais dois ficheiros '
        'novos, <font face="Courier">valves.csv</font> e <font face="Courier">tests.csv</font>), '
        'por isso a primeira execução do <font face="Courier">snapshot.py</font> depois de '
        'actualizar vai mostrar uma diferença grande nesse ficheiro mesmo que não tenha '
        'alterado nada - são o cabeçalho e os campos novos vazios, e não dados perdidos.',
})
