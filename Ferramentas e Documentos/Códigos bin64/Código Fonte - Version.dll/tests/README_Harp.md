# Harpa: tipo de arma novo no cliente

O cliente Classic 5.0 x64 não tem harpa. O enum de tipo de arma do `Game.dll` vai de 1 a 18
(1–14 as armas de combate, 15–18 as ferramentas de coleta), e o número que a harpa tem no Live
5.8, o 8, pertence aqui à lâmina em corrente (`2h_blade`). Estes hooks acrescentam a harpa como
**tipo 19**, sem alterar o `Game.dll` em disco: o `version.dll` entra em seis funções dele por
Detours (`src/AionVersionDll/harp_fix.h`).

O comportamento de referência é sempre o do tipo 8 no `Game.dll` do Live 5.8, lido de um dump
de memória daquele cliente.

Estado: em teste no cliente de teste, só no **bin64**, com o Elyos masculino. Sem commit.

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

## Os seis hooks

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

Para qualquer outro tipo, os seis chamam a função original e devolvem o resultado dela sem
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

## O que os hooks não fazem sozinhos

O `Game.dll` só aponta nomes; os arquivos precisam existir no cliente. Tudo abaixo é dado, posto
no cliente de teste por `Ferramentas Python/teste_harpa_58.py` a partir de um cliente Live 5.8:

| Dado | Onde | Observação |
|---|---|---|
| Item com `<weapon_type>2h_harp</weapon_type>` | `client_items.xml` (4 paks) | hoje só o item de teste `100599901` |
| Mesh, texturas, ícone e a varinha padrão | `objects\items`, `data\items` | `HA_C001`, `Ha_test_stick` |
| Animações `*_harp_*` | `objects\pc\lm\animation` | 217 arquivos |
| Lista de animações do modelo | `lm.cal` e `lm.cab` | o jogo usa o `.cab`, cifrado (ver `aion_cab.py`) |
| Marcadores das animações | `data\AnimationMarkers\lm.xml` | instante de sacar/guardar, ponto de acerto, sons |
| Projétil e efeito de acerto | `Effects\Effects_Meshes.pak` | registro com tamanho diferente no 5.8 (ver `aion_fx.py`) |
| Sons | `sounds\motion`, `sounds\effect\artist` | |

## Pendências conhecidas

- **Outros leitores do tipo de arma.** O campo `item + 0x1C7` é lido em cerca de 80 pontos do
  `Game.dll`. Só os seis acima foram tratados. Faltam, entre outros: as janelas de prévia do
  personagem (`0xA805D0`), a animação de dano (`0x9456F0`, com lista própria de sufixos) e o
  requisito de arma das skills (`required_harp`).
- **Dedos.** O esqueleto do 5.8 tem cinco dedos de três falanges e o do 5.0 três de duas, com
  outra pose de referência. As animações de harpa precisam de conversão nas trilhas de dedo;
  há duas variantes em avaliação, nenhuma fixada.
- **Outras raças e sexos.** Só o Elyos masculino tem animações, lista e marcadores.
- **Servidor.** O item de teste ainda usa o grupo de orbe no emulador.
- **Mão do ataque básico.** O cliente escolhe `cattack_harp_001` ou `_002` pelo campo de mão do
  `S_ATTACK`; o emulador sorteia 1/2 pelo id do item de teste (`CreatureController`), até existir
  o grupo `HARP` no servidor.

## Testes

Ainda não há teste nativo, como os de `quna_fix_checks` e `siel_hammer_fix_checks`. A
verificação até aqui foi em jogo, um hook por vez:

| Hook | Resultado em jogo |
|---|---|
| 1 e 2 | animações de harpa tocam pelo tipo 19 |
| 3 | harpa no braço esquerdo sacada e nas costas guardada |
| 4 e 5 | varinha na mão direita, some ao guardar, equipar e desequipar corretos |
| 6 | nota musical sai no ataque básico, com som e efeito de acerto, sem crash |
