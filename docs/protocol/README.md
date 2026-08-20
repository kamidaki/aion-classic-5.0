# Tabela de opcodes — Aion Classic 4.5 (GameForge)

## Origem

Extraída estaticamente de `G:\GFAion\aionclassic\bin64\Game.dll.bak`
(`ProductVersion 4526.0820.0706.7137`, x64, cliente GameForge EU).

**Não veio de sniffer.** O `Game.dll` está empacotado com um protector estilo
Themida (seções `pdcrczxf` / `xreiptzs` / `.taggant`), mas a seção principal
permanece em texto claro, e nela está a função de inicialização que registra
todos os pacotes do protocolo.

## Estrutura encontrada

Região `0x6d89bb .. 0x6e19fc` do arquivo — **584 registros consecutivos**,
em ordem crescente de opcode, terminando em `C_PROTOCOL_MAX`.

Cada registro emite duas instruções que podem ser pareadas:

```asm
lea   rdx, [rip+disp32]          ; -> string "S_XXX" / "C_XXX"
mov   dword ptr [rsp+30h], imm32 ; imm32 == número do opcode
```

O compilador alterna entre duas alocações de registrador/pilha:

| forma | lea | escrita do imediato |
|---|---|---|
| A (251×) | `48 8D 15` → `rdx` | `C7 44 24 30 <imm32>` (`[rsp+30h]`) |
| B (344×) | `4C 8D 05` → `r8`  | `C7 85 <disp32> <imm32>` (`[rbp+disp32]`) |

Em ~9 casos o `mov` é emitido *antes* do `lea`; o extrator faz fallback para trás.

## Resultado

| | opcodes | faixa |
|---|---|---|
| servidor → cliente | **340** | `0x000` … `0x1b3` (`S_PROTOCOL_MAX`) |
| cliente → servidor | **244** | `0x000` … `0x147` (`C_PROTOCOL_MAX`) |

584 strings encontradas, 584 resolvidas — cobertura total, sem colisões.

> Cuidado com o comprimento mínimo ao varrer strings: `S_DP` tem só 4 caracteres
> e ficou de fora numa primeira versão do extrator, deixando `0x06` falsamente
> vazio e deslocando a leitura de tudo em volta. A sequência de imediatos na
> região de registro é contígua (`0,1,2,3,…`) — use isso como teste de sanidade.

## Validação cruzada

Comparado com um dump independente de Classic **2.5**
(`G:\CodexHELPER\ClaudeAion\aion-main\docs\net_*_opcodes.csv`):

| | idênticos | deslocados | removidos | novos em 4.5 |
|---|---|---|---|---|
| servidor | 293 | 5 | 1 | 41 |
| cliente  | 212 | 4 | 0 | 28 |

Perfil exatamente esperado entre duas versões vizinhas do protocolo — confirma
que a leitura é da tabela real. Deslocamentos notáveis:

* `S_DP` `0x06 → 0x07`, `S_GATHER` `0x23 → 0x22`, `S_COMBINE` `0xb4 → 0xb3`
* `C_SAVE` `0x28 → 0x0a`, `C_PARTY` `0x60 → 0x4d`, `C_FUNCTIONAL_PET` `0x16 → 0x15`

> Nunca reaproveite opcodes de 2.5, de emuladores retail ou de outra build sem
> reconferir aqui. A maioria bate, mas os poucos que deslocaram são justamente
> os que causam desync silencioso.

## Âncoras do fluxo de entrada no mundo

| pacote | opcode |
|---|---|
| `S_VERSION_CHECK` | `0x000` |
| `S_LOGIN_CHECK` | `0x009` |
| `S_ENTER_WORLD_CHECK` | `0x00d` |
| `S_WORLD` | `0x00f` |
| `S_PUT_USER` | `0x020` |
| `S_KEY` | `0x047` |
| `S_L2AUTH_LOGIN_CHECK` | `0x0c6` |
| `S_READY_ENTER_WORLD` | `0x11d` |
| `C_VERSION` | `0x000` |
| `C_ENTER_WORLD` | `0x008` |
| `C_LEVEL_READY` | `0x009` |
| `C_CHARACTER_LIST` | `0x096` |

## Regerar

```bash
python tools/extract_opcodes.py "G:/GFAion/aionclassic/bin64/Game.dll.bak" -o docs/protocol
```

Rode de novo a cada patch do cliente — a GameForge desloca opcodes entre builds.

## Limites

Funciona **apenas** no `Game.dll` x64 do GFAion Classic. Testado e falha em:

* `bin32/Game.dll` (mesma build, 32-bit) — tabela não fica em texto claro
* `AionOrigin/bin64/Game.dll` (4515) — protector NCSoft `.aion0`/`.aion1`
* `Aion Riftshade/bin64/Game.dll` (5818) — só 9 strings vazam

O que a tabela **não** dá: o *layout dos campos* de cada pacote. Isso ainda sai
de RE do handler + captura. A tabela diz *qual* pacote é; a captura diz *o que
tem dentro*.

---

## Confronto com a tabela do Aion-Lightning (retail 4.5)

O AL que estamos usando como base já declara seus opcodes marcados `// 4.5`,
mas é **retail** 4.5, não Classic. Cruzando as duas tabelas pelos nomes que
casam 1:1 (`SM_KEY` ↔ `S_KEY`, `CM_ENTER_WORLD` ↔ `C_ENTER_WORLD`, …):

| lado | nomes comparáveis | opcode idêntico | opcode diferente |
|---|---|---|---|
| servidor (`SM_`) | 22 | **9** | 13 |
| cliente (`CM_`) | 16 | **0** | 16 |

### Servidor: perto, mas não igual

A maioria das divergências é um deslocamento de −1 a partir de `0x42`
(retail tem um pacote a mais no início que o Classic não tem):

```
SM_KEY                0x048 -> 0x047      SM_L2AUTH_LOGIN_CHECK  0x0c7 -> 0x0c6
SM_CAPTCHA            0x057 -> 0x056      SM_CHARACTER_LIST      0x0c8 -> 0x0c7
SM_WEATHER            0x043 -> 0x042      SM_CREATE_CHARACTER    0x0c9 -> 0x0c8
```

Mas há realocações de verdade, que um deslocamento constante não explica:

```
SM_GROUP_INFO         0x05a -> 0x0f7
SM_GROUP_MEMBER_INFO  0x05b -> 0x0f8
```

### Cliente: numeração totalmente diferente

Zero coincidências. O retail embaralha os opcodes de cliente a cada versão; o
Classic usa a tabela sequencial crua:

```
CM_ENTER_WORLD    AL 0x0aa -> Classic 0x008
CM_LEVEL_READY    AL 0x0ab -> Classic 0x009
CM_ATTACK         AL 0x0e2 -> Classic 0x020
CM_CHARACTER_LIST AL 0x174 -> Classic 0x096
```

**Consequência prática:** a tabela de opcodes de cliente do AL é descartada
inteira e reconstruída a partir daqui. A de servidor é auditada pacote a pacote.

### O que isto ainda não resolve

Opcode certo não significa pacote certo. O *corpo* de cada pacote também mudou
entre retail 4.5 e Classic 4.5 — campos a mais, a menos, reordenados. A tabela
diz **qual** pacote é; descobrir **o que tem dentro** continua sendo trabalho de
RE do handler + captura de tráfego.
