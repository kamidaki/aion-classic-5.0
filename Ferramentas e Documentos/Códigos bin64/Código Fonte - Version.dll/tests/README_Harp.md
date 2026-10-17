# Harpa: tipo de arma novo no cliente

O cliente Classic 5.0 x64 não tem harpa. O enum de tipo de arma do `Game.dll` vai de 1 a 18
(1–14 as armas de combate, 15–18 as ferramentas de coleta), e o número que a harpa tem no Live
5.8, o 8, pertence aqui à lâmina em corrente (`2h_blade`). Estes hooks acrescentam a harpa como
**tipo 19**, sem alterar o `Game.dll` em disco: o `version.dll` entra em seis funções dele por
Detours (`src/AionVersionDll/harp_fix.h`).

O comportamento de referência é sempre o do tipo 8 no `Game.dll` do Live 5.8, lido de um dump
de memória daquele cliente.

Estado: em teste no cliente de teste, só no **bin64**. as quatro raças testadas em jogo (LF, DM e DF com `--racas`).

## Enum de tipo de arma no 5.0

| # | Nome no XML | # | Nome no XML |
|---|---|---|---|
| 1 | `1h_sword` | 10 | `2h_book` |
| 2 | `1h_dagger` | 11 | `2h_dimensionsword` |
| 3 | `1h_mace` | 12 | `1h_gun` |
| 4 | `1h_gauntlet` | 13 | `bow` |
| 5 | `2h_sword` | 14 | `2h_runesword` |
| 6 | `2h_polearm` | 15 | `1h_toolhoe` |
| 7 | `2h_staff` | 16 | `2h_toolpick` |
| 8 | `2h_blade` | 17 | `2h_toolrod` |
| 9 | `2h_orb` | 18 | `2h_toolaxe` |

O tipo fica num byte do registro do item em memória (`item + 0x1C7`).

## Os hooks

Os endereços são RVA neste build do `Game.dll` (MD5 `c6b7cfe04ccfdead16695d988e48058d`). A
instalação não usa endereço fixo: procura a assinatura de cada função e só instala se cada uma
aparecer uma única vez.

| # | Função do `Game.dll` | RVA | O que o hook faz para o tipo 19 |
|---|---|---|---|
| 1 | Parser do campo `<weapon_type>` do `client_items.xml` | `0x7DCD90` | `2h_harp` passa a valer 19 |
| 2 | Sufixo do nome da animação por tipo | `0x3B9330` | devolve `_harp` |
| 3 | Osso em que a mesh da arma é presa | `0x2833A0` | regra da harpa (abaixo) |
| 4 | Prende a mesh de uma mão no personagem | `0x38D5D0` | cria a segunda mesh, a varinha |
| 5 | Monta o caminho da mesh da arma | `0x285320` | segunda mesh = `<mesh>_stick.cgf` |
| 6 | Prepara o ataque básico à distância | `0x912A70` | efeito de acerto `sys_hit.hit.harp` |
| 7 | Nome do tipo de arma no tooltip | `0x582FB0` | string `STR_TOOLTIP_HARP` (id 1990001) |
| 8 | Nome da animação de dano | `0x9456F0` | `csdamage_harp_001` |
| — | Tabelas de bônus de encantamento (dados) | `0x1527A90`, `0x1527B30` | índice 19 = o do orbe |

Para qualquer outro tipo, os hooks chamam a função original e devolvem o resultado dela sem
mexer.

### 1. Nome do tipo (`0x7DCD90`)

`int f(const wchar_t* nome)`. A função percorre uma tabela `{nome, valor}` (em `0x10771D0`) e
devolve 0 para nome desconhecido. O hook compara com `2h_harp` antes e devolve 19.

### 2. Sufixo de animação (`0x3B9330`)

`f(int duasArmas, int tipo, char* saida, size_t tamanho)`. É uma tabela de salto de 0 a 18;
acima disso o sufixo sai vazio. O hook escreve `_harp`. O cliente monta o nome lógico da
animação com esse sufixo (`cidle` + `_harp` + `_001`) e o procura na lista do modelo.

### 3. Osso de fixação (`0x2833A0`)

`f(int itemId, int estado, int mao, int flag, char* saida, int tamanho)`. `mao` 0 é a mesh
principal e 1 a segunda; `estado` 1 e 5 são arma sacada. Para tipo desconhecido o cliente
responde `Rhand_bone` com a arma sacada e osso vazio com ela guardada (a arma some).

| Situação | Harpa (mão 0) | Varinha (mão 1) |
|---|---|---|
| Sacada | `Lhand_bone` | `Rhand_bone` |
| Guardada | `Lback_bone` | sem osso (escondida) |

Quando o próprio item nomeia o osso, o lado é espelhado ao contrário das outras armas: mão 0
troca `R` por `L`, mão 1 troca `L` por `R`.

### 4. Segunda mesh (`0x38D5D0`)

`f(personagem, int modo, int ?, int itemId, char direita)`. Quem atualiza as armas do personagem
(`0x38BD40`) chama esta função duas vezes: item da mão principal com `direita = 1`, depois o da
mão secundária com `direita = 0`. Para a lâmina em corrente ele repete o item principal na
segunda chamada, sem olhar o estado da arma (`cmp esi, 8; cmove edi, r14d`). O hook faz o mesmo
para a harpa: se a primeira chamada foi com uma harpa e a segunda veio sem item, passa o item da
harpa. Com a arma guardada a varinha fica sem osso (hook 3) e some. Uma segunda chamada sem item
solta o anexo daquela mao: a previa da criacao termina com uma assim (modo 2, estado 0), e a antiga
condicao "so com a arma sacada" fazia a varinha sumir la.

### 5. Caminho da segunda mesh (`0x285320`)

`f(int itemId, char direita, int ?, int ?, const char* sufixo, char* saida)`. Para os tipos 4 e
8 a função troca `.cgf` por `_r.cgf` / `_l.cgf`. Para a harpa com `direita = 0` o hook troca por
`_stick.cgf`; se esse arquivo não existe, usa `Objects/Items/Ha_test_stick.cgf`, a varinha
padrão do Live. A checagem de existência é a do próprio cliente (`0x426C10`).

### 6. Efeito de acerto do ataque básico (`0x912A70`)

`f(int mao, int ?, int ?, personagem, <sem uso>, tiro)`: o tiro é o **sexto** argumento (o único chamador deixa o quinto sem valor). O projétil vem do item (`ammo_fx`, `ammo_bone`,
`ammo_speed`) para qualquer tipo; o efeito no ponto de acerto é escolhido pelo tipo de arma, só
para orbe, livro, pistola e arco. O hook preenche `sys_hit.hit.harp` (em `tiro + 0x20`) quando a
arma da mão é uma harpa e a função original deixou o campo vazio.

### 7. Nome do tipo no tooltip (`0x582FB0`)

`const wchar_t* f(int tipo)`: tabela de salto de 1 a 18, cada caso busca uma `STR_TOOLTIP_*` na
tabela de strings; acima disso devolve nulo e o tooltip fica sem o tipo. O hook faz a mesma busca
(as três chamadas do primeiro caso, em +0x31, +0x3E e +0x4B) com o id 1990001. O 5.8 chama essa
string `STR_TOOLTIP_HARP` com o id 904448, que no 5.0 já é outra string; a faixa 1.900.000 a
2.199.999 está livre em todas as línguas. O texto vem dos dados (`teste_harpa_58.py --strings`):
"Harp" (o do Live), "Harpa", "Harfe", "Harpe".

### 8. Animação de dano (`0x9456F0`)

`f(personagem, ?, char saida[0x100])`. Com a arma sacada monta `c` + `sdamage` + sufixo + `_001`
a partir de uma lista própria de sufixos, sem a harpa; o 19 caía em `csdamage_noweapon_001`. O
hook escreve `csdamage_harp_001` quando a mão principal é harpa e a secundária vazia, com a
mesma regra da original: só se o modelo tem a animação (chamadas em +0x2D5 e +0x2E5).

### Bônus de encantamento no tooltip

Duas tabelas estáticas `{por nível até +10, por nível acima}` por tipo de arma, com 20 posições:
ataque em `0x1527A90` e magic boost em `0x1527B30`. A 19 fica zerada. O servidor encanta `HARP`
igual a `ORB` (`enchant_templates.xml`: 4 de ataque e 20 de magic boost por nível), então a
entrada do orbe (4/6 e 20/30) é copiada para a 19. A cópia é feita no primeiro uso (parser do
`weapon_type` ou nome do tipo no tooltip): quando os hooks são instalados, os inicializadores do
`Game.dll` podem ainda não ter rodado e as tabelas estão zeradas. As tabelas são achadas pelo código do tooltip
que as carrega (`lea r12`/`lea r13`); o inicializador delas se repete em centenas de unidades
de compilação e não serve de assinatura. O 5.8 não tem essas tabelas.

## Os outros leitores do tipo de arma

O byte `item + 0x1C7` é lido em 133 pontos de 52 funções, e o tipo guardado no personagem
(`+0x384` mão principal, `+0x388` secundária) em mais alguns. Conferidos um a um, com o dump do
5.8 (onde a harpa é o tipo 8) quando houve dúvida:

| Onde | O que faz | Com o tipo 19 |
|---|---|---|
| `0x1E6B20`, `0x319EC0`, `0x5D93A0`, `0x6FA280`, `0x933690` | nome de animação pelo sufixo | hook 2 |
| `0x1794E0`, `0x38AD50`, `0x38AE00` | guardam o tipo no personagem | sem mudança |
| `0x1A3570`, `0x3A6270`, `0x4D1D20`, `0x782EA0`, `0x592C40`, `0x388040`, `0x38DCC0` | comparam o tipo de dois itens | sem mudança |
| `0x585EF0`…`0x58CCF0` | tooltip de encantamento | tabelas acima |
| `0x4083B0`, `0x5859E0` | texto do tipo (busca, tooltip) | hook 7 |
| `0x912F80` | efeito de acerto corpo a corpo | nenhum, igual ao livro e ao 5.8 |
| `0xA805D0`, `0xA804A0` | prévia do personagem | usa os hooks 3 e 5 |
| `0x38B963`, `0x9FEA2B`, `0x287390`, `0x9FE850`, `0xA81EC0`, `0xA82260` | casos de lâmina em corrente (8), pistola (12), espada rúnica (14) | não se aplica |
| `0x388350` | esconde o escudo com arma de duas mãos | o 5.8 inclui a harpa; sem efeito, o servidor não deixa escudo com ela |
| `0x8E2730` | arco (13) | não se aplica |
| `0x166420` | só testa se é arma | sem mudança |
| `0xB2FF50` | requisito de arma da skill: vetor de 19 posições no template | o 19 lê o campo seguinte (`required_shield`): a harpa não libera skill de outra arma, mas `required_harp` precisa de hook (fase das skills) |

## O que os hooks não fazem sozinhos

O `Game.dll` só aponta nomes; os arquivos precisam existir no cliente. Tudo abaixo é dado, posto
no cliente de teste por `Ferramentas Python/teste_harpa_58.py` a partir de um cliente Live 5.8:

| Dado | Onde | Observação |
|---|---|---|
| Item com `<weapon_type>2h_harp</weapon_type>` | `client_items.xml` (4 paks) | hoje só o item de teste `100599901` |
| Mesh, texturas, ícone e a varinha padrão | `objects\items`, `data\items` | `HA_C001`, `Ha_test_stick` |
| Animações `*_harp_*` | `objects\pc\lm\animation` e `objects\pc\lf\animation` | 217 do LM e 220 do LF; o DM usa as do LM e o DF as do LF, como no 5.8 |
| Lista de animações do modelo | `<raça>.cal` e `<raça>.cab` das quatro raças | o jogo usa o `.cab`, cifrado (ver `aion_cab.py`) |
| Marcadores das animações | `data\AnimationMarkers\<raça>.xml` | instante de sacar/guardar, ponto de acerto, sons |
| Projétil e efeito de acerto | `Effects\Effects_Meshes.pak` | registro com tamanho diferente no 5.8 (ver `aion_fx.py`) |
| Sons | `sounds\motion`, `sounds\effect\artist` | |
| Nome do tipo (`STR_TOOLTIP_HARP`, id 1990001) | `client_strings_ui.xml` das 4 línguas | `--strings` |
| Nome do item de teste (`STR_TEST_HARP_58`, id 1990002) | `client_strings_item.xml` das 4 línguas | `--strings`; o `desc` do item aponta para ela |

## Classe Bard (ids 17 e 20)

O cliente 5.0 conhece classes de 0 a 26: varios pontos do `Game.dll` barram ids acima de 26
(`cmp classe, 1Ah; ja`), e os vagos 14, 17, 20 e 23 ja tem lugar, vazio ou copiado do vizinho,
em todas as tabelas por classe. No Live 5.8 o Bard e a especializacao da base `artist`; aqui
`artist` = 17 (base, nao jogavel) e `bard` = 20. Nesta versao nao ha ascensao: o personagem nasce
na classe avancada.

| Onde | O que faz | Para 17/20 |
|---|---|---|
| `0xA3A2F0` (hook) | nome da classe (`STR_CLASS_NAME_*`) | strings 1990003 "Muse" / 1990004 "Songweaver" |
| `0x366340`, `0x366490` (hooks) | nome em minusculas, char e wchar_t (`[%class]` dos sons, scripts) | `artist` / `bard` (era `none`) |
| `0x649C70` (hook) | monta cada posicao da lista de personagens | aplica as trocas de dados antes |
| tabela de Skins `v4_class_*` (dado) | icone pequeno | `v4_class_artist` / `v4_class_bard` |
| tabela `icon_emblem_<nome>` (dado, preenchida na inicializacao) | emblema grande (alvo, selecao) | `artist` / `bard` (era `battlemaster` / `lumines`) |
| switch do sufixo de animacao `0x931F44` (dado + 2 casos novos) | `Nidle_<classe>_lobby_001` etc. | `_artist` / `_bard`, num trecho alocado logo depois do `Game.dll` |

O trecho dos casos novos do sufixo (`_artist`/`_bard`) tem de ficar ate 2 GB acima da base do
`Game.dll` (a tabela de saltos guarda deslocamentos de 32 bits). O `Game.dll` carrega baixo (`0x4C...`),
entre outros modulos e heaps, e os 256 MB seguintes as vezes estavam todos ocupados: sem trecho, o
Bard ficava a sessao inteira sem a animacao da selecao. O `HarpAllocateNear` percorre as regioes
livres com `VirtualQuery` em toda a faixa.

**Escrever no `Game.dll` durante o carregamento quebra o jogo:** o protetor (WinLicense) faz a
inicializacao falhar (erro 1114, "Cannot find NCCrashReporter.dll"). Todo dado e escrito depois:
quando o `LoadLibrary` do `Game.dll` retorna, antes de montar a lista de personagens ou no primeiro
uso de outro hook -- o que vier primeiro.

Dados (`teste_harpa_58.py`):

| Passo | O que grava |
|---|---|
| `--strings` / `--icone-classe` | strings (tipo, classes, item), emblemas do 5.8 e os Skins/`Preset v4_class_icon` 17/20 nas 5 copias do `version4.xml` |
| `--classe-animacoes` | 82 entradas por raca (selecao, criacao, idle no mundo) e os `.caf` que faltam, com a mesma correcao dos dedos |
| `--vozes` | `vlogin2_bard_*` / `vlogin2_artist_*` (32, em ingles) nos paks de voz |
| `--efeito` | `FC_Sys_LoginStage.AR.*`, particulas `sys_lobby.Bard.*` e `skill_ba_songofrest` (fechamento transitivo das citadas), materiais `.fxm`, o modelo `string_FX` e texturas -- junto com o projetil da harpa |

O `.fxm` (material de efeito) tem o mesmo leiaute nas duas versoes (registro de 1936 bytes); os
campos que diferem nos registros comuns sao lixo de memoria no 5.0 e zero no 5.8. So o 4o byte do
cabecalho muda (0 no 5.0, `h` no 5.8).

No servidor: `ARTIST(17)` e `BARD(20)` no fim do `PlayerClass` (o `restrict` dos itens e indexado
pelo `ordinal()`), atributos provisorios iguais aos do `LUMINESS`; `//set class` sem a validacao
de ascensao.

### Tela de criacao

Os botoes `class_1`..`class_13` (`UI_Create.xml`) ficam num vetor fixo de 13 na janela (`+578h`);
a posicao do botao (0..12) vira classe num switch (`0x9CBD50`: 10 -> 19 Luminess). O botao do Bard
(`class_14`, dado novo) nao entra no vetor: o clique liga o "modo Bard" e seleciona a posicao 10,
que com o modo ligado vale 20.

| Onde | O que faz | Para o Bard |
|---|---|---|
| `0x1EF120` (hook) | monta a janela, acha `class_1..13` | acha o `class_14` com a mesma busca e cast |
| `0x1EF5D0` (hook) | comandos da janela (`sel_class`) | clique no `class_14` -> modo Bard + selecao da posicao 10 **pelo hook** da selecao |
| `0x1EFA80` (hook) | selecao: acende o botao da posicao, painel, previa | acende o do Bard e apaga o da posicao 10 |
| `0x9CBD50` / `0x9CBC80` (hooks) | posicao <-> classe | 10 -> 20 no modo Bard; 20 -> posicao 10 |
| `0x999F80` (hook) | indice da previa por classe/raca/sexo | 20 usa o da posicao 10 (61/62 luz, 87/88 sombra) |
| `0x99D1E0` / `0x99C9F0` (hooks) | carregam pontos e cameras das entidades do mapa `login` | guardam os do Bard (`CLASS_Position_L26/L27/D26/D27`, `Camera_<Light|Dark>_Bard_M/F`) |
| `0x998C80` (hook) | roupa da previa, fixa por classe (ids de item por parte) | classe 20: roupa provisoria (Luminess fem. / Sorcerer masc.) e a harpa oficial da raca na parte 0 |
| `0x998500` / `0x999840` | solta uma previa / cria as que faltam | chamados ao entrar e sair do modo Bard |
| `0xA64B00` (hook) | nome de classe -> id ao ler os XMLs (tabela **wchar_t**, `_wcsicmp`; desconhecido = 1Bh) | `artist` = 17, `bard` = 20 |

O painel da direita le o `client_character_class_info.xml` (`data\PC\PC.pak` e
`data\PC\special\special.pak`) pela tabela 87h, procurando pelo id de classe (`0x1D5710`,
registros de 5Ch: `+4` id convertido do `class_name`, `+8..+1C` atributos, `+20` etiquetas, `+58`
descricao). A entrada do Bard (`--painel-criacao`) tem `class_name` "Bard", atributos do
`PlayerClass.BARD`, etiquetas magical/heal/buff/middledistance e a string 1990005
`STR_UI_Bard_DETAIL` (nossa: o 5.8 nao tem essa tela). Sem `skill_info_list` (nao ha videos).

**Cache das tabelas:** o cliente guarda as tabelas ja convertidas em `data\dump\tables.dmp` e, com
`ValidTableDump=1` no `data\dump\config.ini`, nao rele os XMLs nem chama o `0xA64B00`. Um cache
montado com o hook errado continua valendo ate ser invalidado; o `teste_harpa_58.py` poe
`ValidTableDump=0` toda vez que grava um pak.

### Previa 3D na criacao

Cada posicao de botao tem um personagem de previa por raca e sexo (`0x15F6620`, 98 entradas: luz
41 + 2 x posicao + sexo, sombra 67 + ...). O construtor (`0x999840`) cria os que faltam da raca
atual no ponto do mapa `levels\login` da posicao (`CLASS_Position_L01..D25`, os dois sexos no mesmo
ponto: a animacao de criacao os separa), com a classe da posicao e a roupa fixa da classe; a
selecao enquadra com a camera de indice previa - 10. Pontos e cameras sao entidades do mapa,
lidas pelo nome (`0x99D1E0` e `0x99C9F0`, que param na primeira linha com a marca 1).

O Bard divide a posicao 10 com a Luminess e tem plataforma propria no mapa
(`teste_harpa_58.py --plataforma-criacao`): um passo depois do Soul Reaper na fileira de baixo,
com o casal do Artist do 5.8 (um ponto por sexo, D11/D12 e `Camera_DarkArtistM/F`), transladado e
com as cameras recuadas pela linha de visao ate a distancia das do Soul Reaper no 5.0. O Elyos
repete o arranjo Asmodiano: as animacoes de criacao LM/LF do 5.8 tem outra pose que as DM/DF
(braco direito 76/81 graus), e o Elyos usa as DM/DF (`CRIACAO_DOS_ELYOS`). No modo Bard o
`harp_fix.h` poe os pontos e cameras do Bard no lugar dos da posicao 10, solta essas previas e
manda criar de novo; ao sair, volta a Luminess. A harpa da previa e a da tela de criacao do 5.8
(`npc_harp_best_01` / `npc_harp_idvritra01a_01`, so no cliente): a animacao de criacao segura o
`Lhand_bone` a 30-40 cm da mao para a origem desses modelos; a `HA_C001` de teste tem outra
origem e fica dentro do corpo da personagem feminina.

Os itens da previa sao clonados de um orbe do Classic. Ao gera-los, o script repoe os campos
`equip_bone` e `combat_equip_bone` com `Lhand_bone`, como nos itens originais do Live 5.8, alem de
`mat_bow_m`; tambem retira `blade_fx` e `trail_tex` herdados do orbe. Esses campos sao exclusivos
dos itens da tela de criacao e nao mudam a harpa de teste equipada no jogo.

Na Elyos feminina, o item da previa e `102099908` com a malha `HA_IDRun01a_ElyosF.cgf`.
Somente o no principal da malha recebe uma rotacao ao redor do eixo longo Y. O angulo vem
da componente Y da diferenca angular entre `Lhand_bone` e `Rhand_bone` nas animacoes oficiais
LF e DF de criacao do Bard. A rotacao usa o centro medio dos vertices da harpa como pivo,
mantendo o instrumento em pe e longe da mao da varinha. Um deslocamento de 6 cm em direcao
a camera deixa a harpa ligeiramente a frente; a pose, a varinha e a camera permanecem
iguais. O Bard masculino Elyos e os Asmodianos
continuam com os itens e malhas anteriores.
Para atualizar um cliente de teste ja preparado, execute `teste_harpa_58.py --corrige-harpa-previa`
e instale a `version.dll` compilada em `bin64`; o script guarda backups `.bak_elyos_harpa` dos
PAKs alterados. Se ja foi instalada uma malha feminina anterior, execute
`teste_harpa_58.py --ajusta-harpa-previa` para trocar somente essa malha.

**Voltar da selecao para a criacao** (f276ae046). A janela de criacao so e montada na primeira vez
(`0x1EF120` roda 1x), mas os carregadores de ponto e camera (`0x99D1E0`/`0x99C9F0`) rodam a cada
entrada e regravam os dados da posicao 10 com os da Luminess por cima da plataforma do Bard, com o
modo Bard ainda ligado (provado por log: create init 1x, loaders de novo com o modo ligado). Com a
plataforma trocada, os ganchos dos carregadores guardam o valor relido como dado da Luminess e
repoem o do Bard (`HarpKeepPlatform`).

**Criacao.** O pacote de criacao ja sai com a classe 20: os personagens criados pela tela ficam
`BARD` no banco. O resto e do servidor (`player_initial_data` e o `startingPlayerClass` do XSD) e
dos dados (set Novice Songweaver), ver `teste_harpa_58.py`.

Falta para a classe: roupa oficial da previa (`rb_*_login_*_02` do 5.8), habilidade de equipar
harpa (`required_harp`), e 4 texturas e o `MON_Kaisinel_MRT.V3.ShockwaveTrap`, que nao existem nem
no 5.8 limpo.

### Itens do Bard (`harp_fix.h`, `teste_harpa_58.py`)

Para o Bard, o cliente mostrava em vermelho (proibido) todo item que nao estava equipado, mas
deixava equipar e usar (o servidor permite). Duas causas no `Game.dll`:

- **A verificacao recusa as classes base.** `0x7E2450 (item, classe)` devolve "nao pode" direto para
  toda classe da mascara `0x4924000` (14, 17, 20, 23, 26) e, para as outras, o byte
  `item + 0x74 + classe`. A mesma mascara aparece em mais 6 lugares, lacos que montam listas de
  classes na interface. O Bard (20) e jogavel: o `harp_fix.h` tira o bit 20 nos 7 lugares
  (`0x4824000`), e so se encontrar exatamente 7. O `artist` (17) continua como base.
- **A tabela de campos do item nao tem `artist`/`bard`.** O `client_items` da o nivel minimo por
  classe num campo por nome (`<warrior>1</warrior>`). A tabela de campos do ItemTable (getter
  `0x7DE7F0`, logo antes do leitor `0x7DE800`) tem entradas `[tipo, nome, (tamanho << 32) | offset,
  0]` e termina num nome vazio. Os campos de classe sao tipo 7, 1 byte em `item + 0x74 + classe`
  (os `*_max` em `+ 0x8F + classe`); os offsets das classes 14, 17, 20, 23 e 26 estao livres. O
  `harp_fix.h` copia a tabela com `artist` (0x85), `bard` (0x88), `artist_max` (0xA0) e `bard_max`
  (0xA3) e aponta o `lea` do getter para a copia.

Dados (`campos_de_classe_do_bard`, no passo de itens do `teste_harpa_58.py`, nos 4 paks com
`client_items.xml`): todo item ganha `artist`/`bard` (e os `*_max`, se tem os de classe). Regra
medida no 5.8:
- item com o mesmo nivel em todas as classes: `bard` = esse nivel (35.829 contra 231);
- item de outras classes (armas, livros de skill): `bard` = 0;
- `artist` = `bard` (99,4%).

O nivel sai sempre dos dados do 5.0, porque o 5.8 mudou o nivel de muitos itens. Do 5.8 vem so se o
Bard pode usar o item, quando ele existe la (`client_items_*.xml` do 5.8 limpo, 167 mil itens). A
harpa e o set Novice Songweaver ficam liberados. No `Items.pak` da Europa: 72.896 itens decididos
pelo 5.8 (69.712 pode, 3.184 nao pode), 6.768 pela regra e 10 do Bard. Testado em jogo.

### Barra de atalhos inicial (`harp_fix.h`, `teste_harpa_58.py --barra-inicial`)

A barra de um personagem novo vem do cliente, porque o servidor nao manda atalhos na criacao. A fonte
e o `pc\client_default_key.xml`: 36 teclas por classe (1-12 a linha de baixo, 13-24 a do Alt,
25-36 a do Ctrl), linhas `[class, key_value, skill_name, dark_race_skill]`. A tabela e indexada pela
posicao da classe na tela de criacao, de 0 a 12:
- o leitor de campos da `DefaultKeyTable` (vtable `+0xA0`, `0x2C6FF0`) converte o `<class>` em posicao
  (`0x9CBDF0`; nome desconhecido vira 0, a posicao do Gladiador);
- o montador da barra (`0x652460`) procura as linhas pela classe do personagem, passando por
  `0x9CBC80`.

O Bard nao tinha posicao nem linhas, e `0x9CBC80` responde 10 (Luminess) para ele, porque a tela de
criacao precisa disso (`HarpClassToSlotHook`). Por isso ele recebia as teclas da Luminess. Agora o
Bard tem a posicao 13 so nessa tabela:
- **Leitor:** um hook do Detours grava 13 nas linhas `<class>Bard</class>`. Tem de ser hook instalado
  na carga: o cliente le essa tabela enquanto o `Game.dll` carrega, antes de a DLL poder gravar no
  codigo. Um redirecionamento da chamada, feito depois, nunca foi alcancado (provado por log e pelo
  registro no `tables.dmp`).
- **Montador:** a chamada `0x652492` e redirecionada depois da carga (ele roda no jogo), e a classe 20
  responde 13. As chamadas da tela de criacao continuam com a posicao da Luminess.

O 5.8 nao tem essa tabela. As 36 linhas do Bard seguem as outras classes: ataque, itens de iniciante,
Mending, Aromatherapy, pegar item, descansar e voltar para casa, e so a skill que o personagem ja tem
ao nascer (Pulse, `Ar_SongofAir_G1`, na tecla 2). Testado em jogo com um Bard novo.

### Skills Charge (`charge_fix.h`)

No Live 5.8 a skill aprendida (estagio 1, `activation_attribute` `Charge`) carrega sozinha os
estagios do `client_skill_charge.xml`. Um segundo aperto dispara o estagio atingido com
`C_FIRE_CHARGE_SKILL`, opcode 234 sem dados. Sem esse aperto, a skill cancela no fim.

O `Game.dll` 5.0 nao tem nada disso:
- sem `ChargeSkillTable`;
- sem os campos `charge_set_name`/`min_charge_time`;
- o leitor de `activation_attribute` (`0xA0E8A1`) so conhece toggle/active/maintain/passive/provoked;
- o 234 esta livre na tabela nome -> opcode dos C_.

Por isso no cliente o estagio 1 e `Active`, e quem carrega e o servidor (`activation="CHARGE"`,
`<skillcharge>` e `skill_charge.xml`). Tres pontos dao o segundo aperto:

| Ponto | O que faz |
|---|---|
| `0x88FDE0` (conexao, buffer, tamanho) | envia todo pacote do cliente antes da cifra; um `C_USE_SKILL` de skill Charge marca o inicio da carga |
| Pacotes do servidor (observador no hook da Quna) | `S_SKILL_CANCELED`/`S_SKILL_SUCCEDED` de quem carrega encerram a marca (golpe com `cancel_rate`, fim do tempo) |
| `0x9A0E30` (personagem, acao, id, ...) | pedido de acao; com acao 2 (usar skill) da skill em carga, manda o 234 e nao deixa o pedido seguir |

**Por que o pedido de acao, e nao o envio.** Durante um cast o 5.0 guarda o novo pedido em
`personagem + 0x1900/0x1908` e so manda o `C_USE_SKILL` depois que o cast termina. Provado por
log: nenhum pacote do cliente durante a carga; o pedido saiu logo depois do `S_SKILL_CANCELED`.

Formato do pacote em claro: `[H tamanho][H op no fio][C 0x6F][H ~op][dados]`, com op no fio =
`(op + 0xC4) ^ 0x36` (conferido nos 6 opcodes C da captura). O 234 vai como `07 00 98 01 6F 67 FE`.

Do lado do servidor:
- o `CM_USE_CHARGE_SKILL` tem de estar no `AionPacketHandlerFactory` (fio 0x198); a tabela
  `AionClientPacketFactory` nao e usada;
- o handler escolhe o estagio pelo tempo carregado.

A tabela de skills Charge do hook e o `bin64\charge_skills.txt` (`skill_id total_ms`), gravado
pelo `bard_skills_58.py`.

Testado em jogo com a Fiery Descant G1:
- disparo com 1,5 s sai o estagio 1;
- disparo com 9,8 s sai o estagio 3;
- sem o segundo aperto, a carga cancela no fim;
- um golpe que interrompe libera o proximo aperto para uma carga nova.

**Cooldown.** O 5.0 so poe o cooldown do `S_SKILL_SUCCEDED` numa skill aprendida. Os estagios 2+
nao sao aprendidos, entao o icone da skill do estagio 1 nao mostrava o cooldown. Depois do disparo
nesses estagios, o servidor (`CreatureController.useChargeSkill`) manda, para as aprendidas do mesmo
`cooldownId`:
- `S_RESET_SKILL_COOLING_TIME` (0x48, `[H skill][C 1]`, no emulador `SM_SUMMON_PANEL_REMOVE`): o
  cliente grava a duracao do template e avisa a barra de atalhos (`0x81BBA0`, a mesma do
  `S_SKILL_SUCCEDED`). O oficial usa esse pacote para o cooldown da skill de invocacao quando o servo
  morre;
- depois o `S_LOAD_SKILL_COOLTIME` (0x33), que acerta o fim com o cooldown do servidor.

So o 0x33 nao basta: ele grava apenas o fim (`0x81BEC0`). Um `S_SKILL_CANCELED` anterior (golpe,
Dodge) deixa a duracao em 0 e o icone fica sem cooldown.

**Barra de carga.** O `skill_delay_dialog` do 5.8 tem a barra `v5_gauge_charge` (cor por estado
1-4) e as bolinhas `v5_gauge_charge_step` (estado 0 = apagada, 1-4 = cores). Tres achados no 5.0:

- O `ui_preload.xml` do 5.0 nao carrega o `version5.xml`; carrega `ver5`, `ver4`, `version3`,
  `version4`, `hud_s1`... Os dois presets so existem no `version5.xml`, entao os widgets ficavam
  sem imagem. O `teste_harpa_58.py` poe os presets e os 9 Skins no `version4.xml`. A textura
  `v5_common.dds` do 5.0 ja tem as imagens.
- O diálogo tem 5 copias: `data\ui\game\game.pak` e `l10n\{ENG,DEU,FRA}\Data\Data.pak` (BXML),
  mais `l10n\BRA\Data\Data.pak` (zip, XML de texto). A barra ganha nome proprio, `charge_gauge`:
  `delay1` o 5.0 ja usa para os itens 165000000-165009999.
- Funcoes de widget:

| O que | Onde |
|---|---|
| Achar filho por nome | vtable `+0x368` (nome, tipo: 0x2010 gauge, 0x2025 static); so procura, devolve 0 se nao achar |
| Visivel | flags em `+0x28`, bit 1 (`not_visible` limpa); vtable `+0xD8` liga bits, `+0xE0` desliga |
| Estado | vtable `+0x110` grava `+0x30`, o mesmo que a `UIActionSetState` faz |
| Maximo / valor da barra | `0xAAD660` / `0xAAD6A0`, lidos das chamadas da propria funcao de quadro |
| Quadro do `DlgSkillDelay` | `0x65F0E0`: duracao em `+0x4F8`, fim em `+0x4FC`, cast mostrado em `+0x500` |

O hook de quadro mostra a barra e as bolinhas durante a carga. Como no 5.8, a barra enche de novo a
cada estagio (tempos do `charge_skills.txt`, escalados pela duracao que o servidor mandou) e muda de
cor: estagio 1 cor 1, 2 cor 2, o ultimo cor 4 (azul). Durante a carga a barra nativa escolhida
(`+0x508/+0x510`, indice em `+0x520`) fica escondida em todo quadro: o cliente a mostra de novo a
cada inicio de cast. Cada carga nova (inicio do `S_USE_SKILL`) reinicia o estado da barra: um
cancelamento fecha o dialogo, e o fim da carga nunca passa pela funcao de quadro.

Atributos da `charge_gauge`:
- `state_depended="True"` (`+0x354`, leitor do XML `0xAFCA50`): o desenho (`0xAACFC0`) usa a imagem
  do estado `+0x30`. Sem ele a imagem sai da fracao preenchida e so o `main_state` 0 aparece;
- `stage="5"` (`+0x328`): quantos retangulos o gauge calcula (`0xAADBF0`), um por estado. Sem ele so
  existe o do estado 0. Sem `gradient`, cada um ocupa a barra toda. O 5.8 usa o mesmo par nos gauges
  com cor por estado (energia do familiar);
- brilho na ponta do preenchimento: o gauge desenha o `skilldelay` quando `+0x898` esta ligado. O
  dialogo liga nas barras dele ao carregar (`0x65F074`); na `charge_gauge` quem liga e a DLL.

**Animacao por estagio.** O cast comeca (`0x923420`) com `SetAction` (`0x960880`: personagem, 1,
0x1C = cast, parametros), que guarda a acao em `+0xBA0/+0xBA4`, os parametros em `+0xBB0..+0xBDB` e
sinaliza `+0xBA8`. No quadro seguinte, `CharacterObject::StartAnimation` (`0x9373A0`) monta o nome
(`ccast_harp_SongBattle01` + variante, `0x936270`) com a variante forcada por `+0xB5D`. A cada
estagio novo a DLL refaz o `SetAction`, com o estagio em `+0xB5D` e a skill do estagio nos parametros
(`+0x08`, guardada em `+0xBB8`): sai o `ccast_..._00N` (o `_003` em loop) e o `cast_fx` do estagio
(`FC_Ba_SongofBattle.G1.cast_lv2/lv3`). No disparo, o servidor manda o estagio no campo de variante
do `SM_CASTSPELL_RESULT` (o mesmo do passo de multicast), e o cliente toca o `cfire_..._00N`.
Atencao: `0x956230` carrega o modelo e nao toca animacao (chamar deixou o personagem invisivel).

**Nome "Fiery Descant 1Stage".** No 5.8 e o nome + estagio + `STR_CHARGE_STEP` (904606, "Stage").
O 5.0 nao tem a string; o `teste_harpa_58.py` poe `STR_CHARGE_STEP` com o id 1990006. A DLL:
- intercepta `UIStatic::SetText` (vtable `+0x288`, `0xB1E380`) no widget do nome (`+0x518`): guarda o
  nome escrito e, com carga pendente, escreve com o estagio (1 no inicio, antes da resposta do
  servidor);
- busca a string como o dialogo busca os textos dele (`0x65F9D7`: gerenciador + `0x10` -> tabela 0
  -> `0xA34F00`);
- conhece o dialogo desde o construtor (`0x65EF10`): na primeira carga depois do login o nome e
  escrito antes do primeiro quadro. Cuidado: `0x65FAF0` e de outro dialogo de cast, nao deste.

**Clarao das bolinhas.** O 5.8 (`0x442470`) toca `sys_UIfx.Charge.basic` na bolinha do estagio
atingido. No 5.0, efeito de widget = `0xB62D90 (widget, nome, 1, 1, &deslocamento, slot, &callback
vazio)`, como o guarda-roupa (`0x6FD212`). As particulas vem do `sys_uifx.prt` do 5.8
(`EFEITOS_DA_CARGA` no `teste_harpa_58.py`). O `sys_UIfx.Charge.last` (brilho em volta da barra no
ultimo estagio) ficou de fora.

Os efeitos ficam no widget ate alguem remover. O gerenciador de efeitos de widget (`0xB618F0`) tem
`+0x08 (widget, 0, 1)`, que limpa antes de tocar (o cliente faz assim em `0x1F90E5`), e
`+0x20 (widget)`, que remove todos (os dialogos chamam ao fechar). A DLL limpa a bolinha antes do
clarao e remove os efeitos quando a barra some.

**Dois `DlgSkillDelay`.** A barra de cast do alvo (`target_delay_dialog`) e da mesma classe e passa
pela mesma funcao de quadro e pelo mesmo `SetText`. Quando um inimigo lancava magia com voce no alvo,
a DLL tratava cada um como "o dialogo" e zerava o estagio a cada quadro. O clarao era tocado de novo a
cada quadro e parecia em loop, empilhado, e o nome podia ir para o dialogo do alvo. So vale o
dialogo que tem a `charge_gauge`; os outros ficam numa lista e sao ignorados. Antes disso foram
descartados, com prova, a particula (a copia crua do `aion_fx` bate 79% com os dados nativos; o
leitor 0x740 do motor, `0x6D5F0` do `Cry3DEngine.dll`, e de arquivos antigos e bate 66%) e o motor
(o efeito nativo do guarda-roupa, tocado na bolinha, termina sozinho em cerca de 1 s).

**Widgets fora da carga.** O dialogo mostra os nossos widgets quando abre para um cast. Por isso, fora
de uma carga, a barra de carga e as bolinhas sao escondidas em todo quadro e no inicio de cada cast
(quando o dialogo escreve o nome), e nao so depois de uma carga. A carga tambem expira com o tempo
total dela mais uma margem.

Testado em jogo: cores, nome, clarao, brilho da ponta, animacoes por estagio, cooldown depois de
Dodge e a barra depois de cancelar.

## Pendências conhecidas

- **Requisito de arma das skills** (`required_harp`, `0xB2FF50`): as skills do Bard (niveis 1-65,
  `bard_skills_58.py`) ja estao no cliente e no servidor, sem exigir a harpa.
- **Skills Charge do Bard**: so a Fiery Descant G1 entrou (`CARGA` no `bard_skills_58.py`).
  Faltam as outras 27 familias (Fiery Descant G2-G12, Soothing Hymn, Dragon Song, Blazing/Fiery
  Requiem, Ba_SongofGravity).
- **Dedos.** O esqueleto do 5.8 tem cinco dedos de três falanges e o do 5.0 três de duas, com
  outra pose de referência. As animações de harpa precisam de conversão nas trilhas de dedo;
  há duas variantes em avaliação, nenhuma fixada.
- **Outras raças e sexos.** LF, DM e DF instalados com `--racas` (dedos na variante só de posição,
  a mesma do LM), testados em jogo.
- **Servidor.** O item de teste usa `item_group="HARP"` no emulador (slot de duas mãos,
  encantamento igual ao orbe, tempos de skill `harp` do `motion_times.xml`) e `desc` = 1990002, a
  mesma string do cliente. O cliente escolhe `cattack_harp_001` ou `_002` pelo campo de mão do
  `S_ATTACK`; o `CreatureController` sorteia 1/2 para toda arma do grupo `HARP`.

## Testes

Ainda não há teste nativo, como os de `quna_fix_checks` e `siel_hammer_fix_checks`. A
verificação até aqui foi em jogo, um hook por vez:

| Hook | Resultado em jogo |
|---|---|
| 1 e 2 | animações de harpa tocam pelo tipo 19 |
| 3 | harpa no braço esquerdo sacada e nas costas guardada |
| 4 e 5 | varinha na mão direita, some ao guardar, equipar e desequipar corretos |
| 6 | nota musical sai no ataque básico, com som e efeito de acerto, sem crash |
| classe Bard (1a) | nome "Songweaver", ícone e emblema (alvo, seleção, primeira exibição), animação, efeito, som e voz da seleção |
| 7, 8 e encantamento | tooltip mostra "Harpa", dano com animação de harpa, bônus de encantamento igual ao do orbe |
