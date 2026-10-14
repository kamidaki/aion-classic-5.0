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
segunda chamada. O hook faz o mesmo para a harpa: se a primeira chamada foi com uma harpa e a
segunda veio sem item, passa o item da harpa, desde que a arma esteja sacada (estado em
`personagem + 0x2D0`).

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
| `0xA805D0`, `0xA804A0` | prévia do personagem | usa os hooks 3 e 5; a varinha não aparece |
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

## Pendências conhecidas

- **Requisito de arma das skills** (`required_harp`, `0xB2FF50`): fica para as skills do Bard.
- **Varinha nas janelas de prévia:** a prévia não passa pelo hook 4.
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
| 7, 8 e encantamento | tooltip mostra "Harpa", dano com animação de harpa, bônus de encantamento igual ao do orbe |
