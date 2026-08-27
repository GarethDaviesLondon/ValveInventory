#!/usr/bin/env python3
"""
guide.py - the in-app user guide, in English and Portuguese.

Lifted out of valves_gui.py so the two languages sit side by side and can be
read against each other. Help > User guide renders whichever matches the
current interface language, in a proportional-font TextWindow.

Keep the two in step by hand: this is a walkthrough of how the tool is used,
not something generated from the code, so a workflow change means editing
both. A section missing from PT falls back to nothing rather than to English
- if you add a section, translate it.
"""

EN = [
    "VALVE INVENTORY - USER GUIDE", "",
    "Two front ends sharing one database: this window, and valves.py on the command "
    "line. Five tabs here - Valves, Bases / Sockets, Browse, Repair Bench, Docs.",
    "",
    "LANGUAGE", "",
    "  The two flags at the top right switch the whole interface between English and "
    "Portuguese - menus, buttons, tab names, column headings, dialogs. The choice is "
    "remembered for next time.",
    "  What does NOT change is the collection itself. Type designations, box names, "
    "makers, origins and your own notes stay exactly as you typed them: a valve is an "
    "EL84 in any language, and a bag labelled \"Saco Pingo Doce\" is called that "
    "because that is what is written on it. Only the tool's own wording moves.",
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
    "WHAT A LOT RECORDS", "",
    "  A lot is one physical batch: this many of this type, in this box. Beyond the "
    "quantity, maker and condition, each lot can record where it actually sits and "
    "where it came from - all optional, fill in as much or as little as suits you:",
    "    Position       where in the box, as a grid reference like B-12",
    "    Type 1 / 2     other designations the valve is marked with (a US number, "
    "a service code) - searchable, so it doesn't matter which one you look it up by",
    "    Origin         bought, inherited, or the set it came out of",
    "    Test values    what it measured on a tester",
    "    Other          anything else: boxed or unboxed, odd printing",
    "  Select a row and click \"Edit lot\" to fill these in or change them later; the "
    "same fields are on the Add stock form and in the upload CSV. Note the two "
    "editors do different jobs: Edit lot changes this one physical lot, while the "
    "panel on the right changes the reference record shared by every lot of that "
    "type. From the command line: valves.py edit <lot id> --position B-12 ... (lot "
    "ids are the ID column of valves.py box / find / show).",
    "",
    "INDIVIDUAL VALVES AND TESTING", "",
    "  A lot is a quantity - \"6 x KT66 in box 8\" - and for most of a collection "
    "that is all it ever needs to be. Where it isn't, select the lot and click "
    "\"Individual valves...\", then \"Track individually\": that creates one row per "
    "valve held, and from then on each valve has its own position on the shelf, its "
    "own serial or date code, its own maker and condition (for a mixed lot), its own "
    "notes, and its own test history. The Ind column on the results table shows how "
    "many of a lot are tracked this way; blank means the lot is still just a quantity. "
    "New lots added with \"Add stock\" are tracked individually from the start unless "
    "you say otherwise on the form.",
    "  The Notes column in that list is what was written about that one valve - a "
    "serial read off the glass, \"no box\", \"another one at home\". It is per valve, "
    "not per lot, which is the point of tracking individually at all.",
    "  \"Record test...\" logs one test of the selected valve. Every reading is "
    "optional - no tester produces all of them - so a row holding a gm figure and a "
    "date is a perfectly good record. What it can hold:",
    "    Conditions     which tester, Va and Vg at test, fixed or auto bias. A gm "
    "figure means nothing without them, and the same valve reads differently under "
    "fixed and auto bias, so the tester and conditions are carried forward from the "
    "valve's last test.",
    "    Readings       anode current Ia (mA), screen current Ig2 (mA), mutual "
    "conductance gm (mA/V - multiply by 1000 for the micromhos an American tester "
    "shows), gm as a percentage of nominal, emission %.",
    "    Fault tests    gas / grid current (uA), insulation (Mohm), heater-cathode "
    "leakage, shorts, and an overall verdict.",
    "  Testing is never destructive: each test is a new row, so retesting a valve "
    "years later builds its history rather than replacing it. \"Test history...\" (or "
    "double-clicking a valve) shows every test of it, newest first. A double triode "
    "is recorded a section at a time - run Record test twice, once with Section a and "
    "once with b, which is how the readings come off the meter and how they have to "
    "be compared for matching. The list shows the most recent test of either section; "
    "the history shows both.",
    "  A test dated 1901-01-01 is one recovered from a written record that gave no "
    "date. Nothing was tested in 1901 - the valve had not been invented - so the date "
    "is a marker meaning \"tested, date unknown\" rather than a real measurement day.",
    "  Amber rows in that list are valves never tested; red-brown are ones whose last "
    "verdict was weak, short or failed.",
    "  Take (on the Valves tab) removes individual rows along with the quantity, "
    "least documented first - untested before tested, unmarked before serial-numbered "
    "- so using valves up never quietly discards test history. \"Remove valve\" in the "
    "dialog is the other thing: it corrects the record without touching the quantity. "
    "Tools > Check individual valve counts reports any lot where the two have drifted "
    "apart.",
    "  From the command line: valves.py expand <lot id>, then lot / valve / test / "
    "tests / check.",
    "",
    "REMOVING / MOVING STOCK", "",
    "  Select a row, then Take (use up some of a lot), Move (to another box, "
    "optionally giving its position there), or Delete lot (removes it - asks first). "
    "Same from the command line: valves.py take/move TYPE ...",
    "",
    "SEARCHING & BROWSING", "",
    "  Valves tab search row - text, function, base, and the numeric fields (accept "
    "'>20', '<7', '>=250'). Text searches the lot's own fields as well as the "
    "reference record, so \"the one out of the Bush\" or a number printed only on the "
    "glass finds it without your having to remember which field you wrote it in. "
    "Searching a type also pulls in anything cross-referenced "
    "as its equivalent, shown in blue and labelled which type it's equivalent to. "
    "Advanced... opens every remaining field, Position, Origin and Type 1 / Type 2 "
    "among them.",
    "  The Tested filter narrows the list to lots that hold at least one tested valve, "
    "or to those that hold none. The Tstd column beside it counts how many valves in "
    "each lot have been tested.",
    "  Browse tab - dropdown filters that cascade (Category, Base, Family, "
    "Confidence, Variable-mu, Tested - picking one narrows what the others offer), "
    "plus <, =, > on every numeric rating, and a live name filter as you type. "
    "Double-click a type for its box breakdown, full reference data, and "
    "datasheet/web-search shortcuts. In that popup, double-click one of the box rows "
    "to drop straight into the individual valves of that lot - the same window the "
    "Valves tab reaches through \"Individual valves...\", so a valve found by browsing "
    "behaves exactly like one found by searching.",
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
    "scoped to that site). The button itself says which it'll do - \"Open datasheet "
    "(local)\" or \"Find datasheet (web)\" - before you click it. Tools > Scan "
    "datasheet archive links newly-added PDF files in by filename. "
    "fetch_datasheets.py builds the archive itself from frank.pocnet.net (see README) "
    "- it's gitignored and not included when you export, so rebuild it locally or use "
    "the download prompt above.",
    "  Manage... (Manage information... on the Browse tab's popup, next to Open "
    "datasheet) opens the full list for a type: the one \"primary\" sheet that button "
    "opens, plus as many extra datasheets and links as you want - a second "
    "manufacturer's sheet, a forum thread, a project that happens to use this valve. "
    "Upload a file you already have, or paste a URL - no download needed for a link, "
    "it's just recorded. Its Edit parameters... button opens the same field-entry form "
    "as the detail panel, so a Browse-tab research session never needs to switch tabs "
    "to record what a datasheet says.",
    "  The Docs tab holds the same idea for material that isn't about one specific "
    "type - a care-and-feeding guide, a base wiring reference. Add from file / Add "
    "from URL, a title and an optional abstract, and a filter box to find things again.",
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
]


PT = [
    "INVENTÁRIO DE VÁLVULAS - GUIA DO UTILIZADOR", "",
    "Duas interfaces sobre a mesma base de dados: esta janela e o valves.py na linha "
    "de comandos. Aqui há cinco separadores - Válvulas, Bases / Suportes, Explorar, "
    "Bancada e Documentos.",
    "",
    "IDIOMA", "",
    "  As duas bandeiras no canto superior direito mudam toda a interface entre inglês "
    "e português - menus, botões, nomes dos separadores, cabeçalhos das colunas e "
    "caixas de diálogo. A escolha fica guardada para a próxima vez.",
    "  O que NÃO muda é a colecção em si. As designações dos tipos, os nomes das "
    "caixas, as marcas, as origens e as suas próprias notas ficam exactamente como as "
    "escreveu: uma válvula é uma EL84 em qualquer idioma, e um saco identificado como "
    "\"Saco Pingo Doce\" chama-se assim porque é isso que lá está escrito. Só muda o "
    "texto da própria ferramenta.",
    "",
    "ADICIONAR EXISTÊNCIAS", "",
    "  Uma de cada vez  \"Adicionar existências\" (separador Válvulas) / \"Adicionar\" "
    "(separador Bases-Suportes). Cria o tipo automaticamente se for novo, "
    "classificando-o a partir da designação.",
    "  Em lote          Ferramentas > Importar CSV..., usando o formato de colunas de "
    "Ferramentas > Criar modelo de importação... (escreve um CSV em branco pronto a "
    "preencher).",
    "  A partir de dados desorganizados  Ferramentas > Gerar instruções para construir "
    "CSV... escreve um texto para colar em qualquer conversa com o Claude. Ele "
    "pergunta-lhe o que precisa (ou lê a folha de cálculo, apontamentos ou fotografias "
    "que lhe descrever) e devolve um CSV pronto a importar.",
    "",
    "O QUE UM LOTE REGISTA", "",
    "  Um lote é um conjunto físico: esta quantidade deste tipo, nesta caixa. Para "
    "além da quantidade, marca e estado, cada lote pode registar onde está realmente "
    "e de onde veio - tudo opcional, preencha tanto ou tão pouco quanto lhe convier:",
    "    Posição        onde está dentro da caixa, como uma referência do tipo B-12",
    "    Tipo 1 / 2     outras designações marcadas na válvula (um número americano, "
    "um código militar) - pesquisáveis, por isso não importa por qual delas procura",
    "    Origem         comprada, herdada, ou o aparelho de onde saiu",
    "    Valores de ensaio  o que mediu no aparelho de ensaio",
    "    Outros         tudo o resto: com ou sem caixa, impressão invulgar",
    "  Seleccione uma linha e clique em \"Editar lote\" para preencher ou alterar estes "
    "campos mais tarde; os mesmos campos estão no formulário de adicionar e no CSV de "
    "importação. Note que os dois editores fazem coisas diferentes: Editar lote altera "
    "este lote físico, enquanto o painel da direita altera o registo de referência "
    "partilhado por todos os lotes desse tipo. Na linha de comandos: valves.py edit "
    "<id do lote> --position B-12 ... (os ids dos lotes são a coluna ID de valves.py "
    "box / find / show).",
    "",
    "VÁLVULAS INDIVIDUAIS E ENSAIOS", "",
    "  Um lote é uma quantidade - \"6 x KT66 na caixa 8\" - e para a maior parte de uma "
    "colecção nunca precisa de ser mais do que isso. Quando precisa, seleccione o lote "
    "e clique em \"Válvulas individuais...\" e depois em \"Registar individualmente\": "
    "isso cria uma linha por cada válvula existente, e a partir daí cada válvula tem a "
    "sua posição na prateleira, o seu número de série ou código de data, a sua marca e "
    "estado (num lote misto), as suas notas e o seu histórico de ensaios. A coluna Ind "
    "na tabela de resultados mostra quantas válvulas de um lote estão registadas "
    "assim; em branco significa que o lote ainda é apenas uma quantidade. Os lotes "
    "novos criados com \"Adicionar existências\" ficam registados individualmente desde "
    "o início, a menos que indique o contrário no formulário.",
    "  A coluna Notas nessa lista é o que foi escrito sobre aquela válvula em concreto "
    "- um número de série lido no vidro, \"sem caixa\", \"outra em casa\". É por "
    "válvula e não por lote, que é precisamente a razão de as registar individualmente.",
    "  \"Registar um ensaio\" regista um ensaio da válvula seleccionada. Todas as "
    "leituras são opcionais - nenhum aparelho de ensaio produz todas - por isso uma "
    "linha com apenas um valor de gm e uma data já é um registo perfeitamente válido. "
    "O que pode conter:",
    "    Condições      qual o aparelho, Va e Vg no ensaio, polarização fixa ou "
    "automática. Um valor de gm não significa nada sem elas, e a mesma válvula lê "
    "valores diferentes com polarização fixa e automática, por isso o aparelho e as "
    "condições são reaproveitados do último ensaio da válvula.",
    "    Leituras       corrente de ânodo Ia (mA), corrente de grelha ecrã Ig2 (mA), "
    "condutância mútua gm (mA/V - multiplique por 1000 para os micromhos que um "
    "aparelho americano mostra), gm em percentagem do nominal, emissão %.",
    "    Ensaios de avaria  corrente de gás / grelha (uA), isolamento (Mohm), fugas "
    "filamento-cátodo, curto-circuitos, e um veredicto global.",
    "  Ensaiar nunca destrói nada: cada ensaio é uma linha nova, por isso voltar a "
    "ensaiar uma válvula anos depois acrescenta ao histórico em vez de o substituir. "
    "\"Histórico de ensaios\" (ou clicar duas vezes numa válvula) mostra todos os "
    "ensaios dela, do mais recente para o mais antigo. Um duplo tríodo regista-se uma "
    "secção de cada vez - faça Registar um ensaio duas vezes, uma com a Secção a e "
    "outra com a b, que é como as leituras saem do aparelho e como têm de ser "
    "comparadas para emparelhar. A lista mostra o ensaio mais recente de qualquer das "
    "secções; o histórico mostra as duas.",
    "  Um ensaio com a data 1901-01-01 é um ensaio recuperado de um registo escrito "
    "que não indicava a data. Nada foi ensaiado em 1901 - a válvula ainda não tinha "
    "sido inventada - por isso a data é uma marca que significa \"ensaiada, data "
    "desconhecida\" e não um dia de medição real.",
    "  As linhas a âmbar nessa lista são válvulas nunca ensaiadas; as castanho-"
    "avermelhadas são aquelas cujo último veredicto foi fraca, curto-circuito ou "
    "avariada.",
    "  Retirar (no separador Válvulas) remove linhas individuais juntamente com a "
    "quantidade, começando pelas menos documentadas - por ensaiar antes das ensaiadas, "
    "sem marcação antes das que têm número de série - para que gastar válvulas nunca "
    "deite fora histórico de ensaios sem avisar. \"Remover válvula\" na caixa de "
    "diálogo é outra coisa: corrige o registo sem mexer na quantidade. Ferramentas > "
    "Verificar contagem de válvulas individuais indica qualquer lote em que as duas "
    "coisas tenham deixado de coincidir.",
    "  Na linha de comandos: valves.py expand <id do lote>, e depois lot / valve / "
    "test / tests / check.",
    "",
    "RETIRAR / MOVER EXISTÊNCIAS", "",
    "  Seleccione uma linha e depois Retirar (gastar parte de um lote), Mover (para "
    "outra caixa, indicando opcionalmente a posição lá dentro) ou Eliminar lote "
    "(remove-o - pergunta primeiro). O mesmo na linha de comandos: valves.py "
    "take/move TIPO ...",
    "",
    "PESQUISAR E EXPLORAR", "",
    "  A linha de pesquisa do separador Válvulas - texto, função, base e os campos "
    "numéricos (aceitam '>20', '<7', '>=250'). O texto procura tanto nos campos do "
    "próprio lote como no registo de referência, por isso \"a que saiu do Bush\" ou um "
    "número impresso só no vidro encontram-se sem ter de se lembrar em que campo o "
    "escreveu. Procurar um tipo traz também tudo o que esteja registado como seu "
    "equivalente, mostrado a azul e indicando de que tipo é equivalente. Avançado... "
    "abre todos os restantes campos, incluindo Posição, Origem e Tipo 1 / Tipo 2.",
    "  O filtro Ensaiada restringe a lista aos lotes que têm pelo menos uma válvula "
    "ensaiada, ou àqueles que não têm nenhuma. A coluna Ens ao lado conta quantas "
    "válvulas de cada lote foram ensaiadas.",
    "  Separador Explorar - filtros em cascata (Categoria, Base, Família, Confiança, "
    "Mu variável, Ensaiada - escolher um estreita o que os outros oferecem), mais <, "
    "=, > em todos os valores numéricos, e um filtro de nome que responde enquanto "
    "escreve. Clique duas vezes num tipo para ver a distribuição por caixas, os dados "
    "de referência completos e os atalhos para a folha de dados e pesquisa na web. "
    "Nessa janela, clique duas vezes numa das linhas de caixa para ir directamente às "
    "válvulas individuais desse lote - a mesma janela a que o separador Válvulas chega "
    "por \"Válvulas individuais...\", para que uma válvula encontrada a explorar se "
    "comporte exactamente como uma encontrada a pesquisar.",
    "",
    "SEPARADOR BANCADA", "",
    "  Para o caso de \"tirei esta válvula de um aparelho que estou a arranjar - o que "
    "é, e o que tenho que a possa substituir?\". Escreva a designação (e, se quiser, "
    "de que andar do circuito veio) e clique em Identificar.",
    "  Se já estiver na sua base de dados, os dados de referência aparecem logo, \"Em "
    "stock agora\" mostra as que já tem desse tipo exacto ou de um equivalente "
    "registado, e \"Substitutos possíveis\" lista outros tipos que possui com a mesma "
    "função geral e todos os valores comuns dentro de 50% (as diferenças de "
    "aquecimento são assinaladas, não escondidas - muitas vezes uma resistência "
    "resolve). Clique duas vezes num substituto para passar a ele.",
    "  Se for nova para si: Abrir folha de dados / RadioMuseum / Pesquisar na web "
    "funcionam logo a partir da designação escrita, e Copiar instruções coloca na área "
    "de transferência uma versão para um único tipo das instruções de pesquisa (ver "
    "abaixo). Adicionar à base de dados cria um registo de referência vazio (sem "
    "existências) para ter onde guardar o que encontrar; Guardar / Guardar + confirmar "
    "funcionam exactamente como no painel de detalhe do separador Válvulas, e "
    "actualizam de imediato a lista de substitutos com os parâmetros que acabou de "
    "introduzir.",
    "",
    "PREENCHER OS DADOS DE REFERÊNCIA", "",
    "  Os parâmetros começam por ser deduzidos da convenção de nomes do tipo, e não "
    "lidos de uma folha de dados - as linhas não confirmadas aparecem a âmbar no "
    "separador Válvulas.",
    "  À mão      Edite os campos no painel de detalhe e depois Guardar + confirmar.",
    "  Com o Claude:",
    "    Ferramentas > Gerar instruções de pesquisa...                 parâmetros "
    "eléctricos",
    "    Ferramentas > Gerar instruções para descarregar folhas de dados...   PDFs "
    "para o arquivo local",
    "  Cole qualquer uma delas no Claude - as instruções de pesquisa funcionam em "
    "qualquer conversa; as de descarregar precisam de um agente com acesso a ficheiros "
    "e à web (Claude Code), porque escrevem ficheiros no disco. Guarde a resposta num "
    "ficheiro de texto e depois use Ferramentas > Aplicar dados pesquisados... (ou "
    "'import_researched.py <ficheiro> --yes' na linha de comandos). Só é aplicado o "
    "que o Claude confirmou de facto - uma conclusão com reservas ('não foi possível "
    "verificar', 'plausível') fica assinalada como pista e não como confirmada.",
    "",
    "FOLHAS DE DADOS", "",
    "  Clicar duas vezes numa linha, ou \"Abrir folha de dados\", abre o PDF local se "
    "existir; caso contrário faz uma pesquisa na web (RadioMuseum / Pesquisar na web "
    "fazem o mesmo, limitado a esse sítio). O próprio botão diz o que vai fazer - "
    "\"Abrir folha de dados (local)\" ou \"Procurar folha de dados (web)\" - antes de "
    "clicar. Ferramentas > Analisar arquivo de folhas de dados liga os PDF novos pelo "
    "nome do ficheiro. O fetch_datasheets.py constrói o próprio arquivo a partir do "
    "frank.pocnet.net (ver README) - está fora do controlo de versões e não vai "
    "incluído na exportação, por isso reconstrua-o localmente ou use as instruções de "
    "descarregar acima.",
    "  Gerir... (Gerir informação... na janela do separador Explorar, ao lado de Abrir "
    "folha de dados) abre a lista completa de um tipo: a folha \"principal\" que aquele "
    "botão abre, mais tantas folhas e ligações adicionais quantas quiser - a folha de "
    "outro fabricante, um tópico de fórum, um projecto que use esta válvula. Carregue "
    "um ficheiro que já tenha, ou cole um URL - para uma ligação não é preciso "
    "descarregar nada, fica apenas registada. O botão Editar parâmetros... abre o mesmo "
    "formulário do painel de detalhe, para que uma sessão de pesquisa no separador "
    "Explorar nunca tenha de mudar de separador para registar o que a folha de dados "
    "diz.",
    "  O separador Documentos faz o mesmo para material que não é sobre um tipo "
    "específico - um guia de utilização, uma referência de ligações de bases. "
    "Adicionar de ficheiro / Adicionar de URL, um título e um resumo opcional, e uma "
    "caixa de filtro para voltar a encontrar as coisas.",
    "",
    "CÓPIAS DE SEGURANÇA E CONTROLO DE VERSÕES", "",
    "  O valves.db é a base de dados viva - está fora do controlo de versões, por ser "
    "binária e não se poder comparar. O snapshot.py escreve data/*.csv e valves.sql, "
    "um retrato em texto que ESSE sim deve ser guardado no controlo de versões - é "
    "essa a verdadeira cópia de segurança e o histórico. Depois de clonar ou restaurar "
    "noutro sítio: 'snapshot.py --restore' reconstrói o valves.db a partir de data/.",
    "",
    "EXPORTAR E DAR ISTO A OUTRA PESSOA", "",
    "  Ficheiro > Exportar folha de cálculo...  um .xlsx simples para quem só quer "
    "ver, sem usar a ferramenta.",
    "  Ficheiro > Exportar arquivo e ferramentas (.zip)...  todo o conjunto (código, "
    "documentação e um retrato novo de data/) num zip, com a opção de retirar antes o "
    "texto descritivo de terceiros. Ver o QUICKSTART.md, incluído no zip:",
    "    1. Descompactar, correr 'python3 snapshot.py --restore' e depois 'python3 "
    "valves_gui.py'.",
    "    2. As folhas de dados não vão incluídas - reconstrua com o fetch_datasheets.py, "
    "ou com Ferramentas > Gerar instruções para descarregar folhas de dados... e o "
    "Claude.",
    "    3. Acrescentar as próprias existências pelas mesmas vias descritas acima.",
    "",
    "Tudo isto funciona também na linha de comandos - ver o README.md para a lista "
    "completa de comandos.",
]

TEXTS = {"en": EN, "pt": PT}


def text(lang="en"):
    """The guide as one string, in `lang` (English for an unknown language)."""
    return "\n".join(TEXTS.get(lang, EN))
