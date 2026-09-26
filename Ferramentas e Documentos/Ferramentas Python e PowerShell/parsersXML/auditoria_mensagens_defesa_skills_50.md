# Auditoria de mensagens e defesas das Skills — Classic 5.0

## Mensagens `???`

O cliente oficial contém **5694 mensagens**. O Java declara **4133 factories**; **334** apontam para IDs inexistentes no cliente Classic 5.0 e **112** delas são chamadas pelo código atual.
Um ID ausente é causa direta e reproduzível para o cliente exibir `???`. Nome divergente com ID existente é risco de texto/parâmetros incorretos, não necessariamente `???`.
Após substituir o ID legado de distância por `STR_SKILL_TOO_FAR` (`1300022`), o motor de Skills possui **0 chamada(s)** para IDs ausentes. As demais chamadas inválidas pertencem a outros subsistemas e não foram alteradas sem correspondência oficial comprovada.

### IDs inexistentes que possuem chamadas

| ID | Factory | Usos |
|---:|---|---:|
| 1402601 | `STR_ATTEND_MSG_ATTEND_REWARD_GET` | 1 |
| 900847 | `STR_BUDDYLIST_BUSY` | 2 |
| 900700 | `STR_GUILD_EVENT_LEVELUP` | 1 |
| 904452 | `STR_GUILD_LEVEL_UP_CHALLENGE_TASK` | 1 |
| 1401239 | `STR_HOUSING_WAREHOUSE_TOO_MANY_ITEMS_WAREHOUSE` | 1 |
| 1402579 | `STR_ITEM_UPGRADE_MSG_UPGRADE_SUCCESS` | 1 |
| 901338 | `STR_LOOT_NO_RIGHT` | 1 |
| 1402251 | `STR_MAIL_TAKE_ALL_CANCEL` | 1 |
| 901354 | `STR_MOVE_PORTAL_ERROR_INVALID_RACE` | 1 |
| 1402573 | `STR_MSG_ATTEND_REWARD_INVALID_LEVEL` | 1 |
| 1402627 | `STR_MSG_ATTEND_REWARD_REMOVE_EXCESS` | 1 |
| 1402237 | `STR_MSG_BREAK_PROC` | 1 |
| 1401294 | `STR_MSG_CANT_USE_HOUSE_OBJECT_ITEM_EQUIP` | 1 |
| 1402878 | `STR_MSG_DARK_SIDE_LEGION_DIRECT_PORTAL_OPEN` | 1 |
| 1402285 | `STR_MSG_ENCHANT_ITEM_SUCCEEDED_20` | 1 |
| 1402674 | `STR_MSG_ENCHANT_TYPE1_ENCHANT_FAIL` | 1 |
| 1402656 | `STR_MSG_EXCEED_ALREADY` | 1 |
| 1402650 | `STR_MSG_EXCEED_CANNOT_01` | 1 |
| 1402661 | `STR_MSG_EXCEED_CANNOT_02` | 2 |
| 1402655 | `STR_MSG_EXCEED_NO_TARGET_ITEM` | 2 |
| 1402662 | `STR_MSG_EXCEED_SKILL_ENCHANT` | 1 |
| 1402657 | `STR_MSG_EXCEED_SUCCEED` | 1 |
| 1402238 | `STR_MSG_GIVE_PROC_CANCEL` | 1 |
| 1402902 | `STR_MSG_GUILD_APPLY_DOMINION` | 1 |
| 1401270 | `STR_MSG_HOUSING_AUCTION_FAIL` | 3 |
| 1401268 | `STR_MSG_HOUSING_AUCTION_MY_HOUSE` | 1 |
| 1401269 | `STR_MSG_HOUSING_AUCTION_SUCCESS` | 2 |
| 1401266 | `STR_MSG_HOUSING_BID_CANCEL` | 2 |
| 1401265 | `STR_MSG_HOUSING_BID_SUCCESS` | 1 |
| 1401267 | `STR_MSG_HOUSING_BID_WIN` | 2 |
| 1401280 | `STR_MSG_HOUSING_CANNOT_USE_FLOWERPOT_COOLTIME` | 1 |
| 1401224 | `STR_MSG_HOUSING_CANT_BID_GRACE_HOUSE` | 1 |
| 1401225 | `STR_MSG_HOUSING_CANT_BID_LOW_LEVEL` | 1 |
| 1401221 | `STR_MSG_HOUSING_CANT_BID_MY_HOUSE` | 1 |
| 1401283 | `STR_MSG_HOUSING_CANT_BID_NOT_ENOUGH_MONEY` | 2 |
| 1401223 | `STR_MSG_HOUSING_CANT_BID_OTHER_HOUSE` | 1 |
| 1401222 | `STR_MSG_HOUSING_CANT_BID_SUCC_BID_HOUSE` | 1 |
| 1401274 | `STR_MSG_HOUSING_CANT_BID_TIMEOUT` | 1 |
| 1401277 | `STR_MSG_HOUSING_CANT_OWN_NOT_COMPLETE_QUEST` | 1 |
| 1401273 | `STR_MSG_HOUSING_GRACE_FAIL` | 1 |
| 1401271 | `STR_MSG_HOUSING_GRACE_START` | 1 |
| 1401272 | `STR_MSG_HOUSING_GRACE_SUCCESS` | 1 |
| 1401276 | `STR_MSG_HOUSING_INS_CANT_OWN_MORE_HOUSE` | 1 |
| 1401275 | `STR_MSG_HOUSING_INS_OWN_SUCCESS` | 1 |
| 1401295 | `STR_MSG_HOUSING_OBJECT_ACHIEVE_USE_COUNT` | 1 |
| 1401296 | `STR_MSG_HOUSING_OBJECT_ALL_CANT_USE` | 2 |
| 1401258 | `STR_MSG_HOUSING_OBJECT_CANCEL_USE` | 1 |
| 1401260 | `STR_MSG_HOUSING_OBJECT_CANT_USE_PER_DAY` | 1 |
| 1401261 | `STR_MSG_HOUSING_OBJECT_DELETE_EXPIRE_TIME` | 2 |
| 1401298 | `STR_MSG_HOUSING_OBJECT_IS_ONLY_FOR_OWNER_VALID` | 2 |
| 1401256 | `STR_MSG_HOUSING_OBJECT_OCCUPIED_BY_OTHER` | 3 |
| 1401263 | `STR_MSG_HOUSING_OBJECT_REWARD_ITEM` | 1 |
| 1401297 | `STR_MSG_HOUSING_OBJECT_TOO_FAR_TO_USE` | 1 |
| 1401257 | `STR_MSG_HOUSING_OBJECT_USE` | 3 |
| 1401226 | `STR_MSG_HOUSING_OVERDUE` | 1 |
| 1401227 | `STR_MSG_HOUSING_SEQUESTRATE` | 2 |
| 1402506 | `STR_MSG_LDF4_ADVANCE_CHIEF_V01` | 1 |
| 1402507 | `STR_MSG_LDF4_ADVANCE_CHIEF_V02` | 1 |
| 1402508 | `STR_MSG_LDF4_ADVANCE_CHIEF_V03` | 1 |
| 1402509 | `STR_MSG_LDF4_ADVANCE_CHIEF_V04` | 1 |
| 1402510 | `STR_MSG_LDF4_ADVANCE_CHIEF_V05` | 1 |
| 1402511 | `STR_MSG_LDF4_ADVANCE_CHIEF_V06` | 1 |
| 1402512 | `STR_MSG_LDF4_ADVANCE_CHIEF_V07` | 1 |
| 1402513 | `STR_MSG_LDF4_ADVANCE_CHIEF_V08` | 1 |
| 1402514 | `STR_MSG_LDF4_ADVANCE_CHIEF_V09` | 1 |
| 1402515 | `STR_MSG_LDF4_ADVANCE_CHIEF_V10` | 1 |
| 1402516 | `STR_MSG_LDF4_ADVANCE_CHIEF_V11` | 1 |
| 1402517 | `STR_MSG_LDF4_ADVANCE_CHIEF_V12` | 1 |
| 1402518 | `STR_MSG_LDF4_ADVANCE_CHIEF_V13` | 1 |
| 1402544 | `STR_MSG_LDF4_ADVANCE_GODELITE_TIME_01` | 1 |
| 1402545 | `STR_MSG_LDF4_ADVANCE_GODELITE_TIME_02` | 1 |
| 1402546 | `STR_MSG_LDF4_ADVANCE_GODELITE_TIME_03` | 1 |
| 1402519 | `STR_MSG_LDF4_ADVANCE_KILLER_V01` | 1 |
| 1402520 | `STR_MSG_LDF4_ADVANCE_KILLER_V02` | 1 |
| 1402521 | `STR_MSG_LDF4_ADVANCE_KILLER_V03` | 1 |
| 1402522 | `STR_MSG_LDF4_ADVANCE_KILLER_V04` | 1 |
| 1402523 | `STR_MSG_LDF4_ADVANCE_KILLER_V05` | 1 |
| 1402524 | `STR_MSG_LDF4_ADVANCE_KILLER_V06` | 1 |
| 1402525 | `STR_MSG_LDF4_ADVANCE_KILLER_V07` | 1 |
| 1402526 | `STR_MSG_LDF4_ADVANCE_KILLER_V08` | 1 |
| 1402527 | `STR_MSG_LDF4_ADVANCE_KILLER_V09` | 1 |
| 1402528 | `STR_MSG_LDF4_ADVANCE_KILLER_V10` | 1 |
| 1402529 | `STR_MSG_LDF4_ADVANCE_KILLER_V11` | 1 |
| 1402530 | `STR_MSG_LDF4_ADVANCE_KILLER_V12` | 1 |
| 1402531 | `STR_MSG_LDF4_ADVANCE_KILLER_V13` | 1 |
| 1402543 | `STR_MSG_LDF4_Advance_GodElite` | 1 |
| 1402877 | `STR_MSG_LIGHT_SIDE_LEGION_DIRECT_PORTAL_OPEN` | 1 |
| 1402666 | `STR_MSG_LIMITED_VENDOR_CANT_OVER_GOLD` | 1 |
| 901285 | `STR_MSG_NOT_ENOUGH_KINA` | 3 |
| 1402931 | `STR_MSG_STIGMA_ENCHANT_FAIL` | 1 |
| 1402930 | `STR_MSG_STIGMA_ENCHANT_SUCCESS` | 1 |
| 1402592 | `STR_MSG_WEAK_RACE_BUFF_DARK_GAIN` | 1 |
| 1402593 | `STR_MSG_WEAK_RACE_BUFF_DARK_GET_OUT_AREA` | 1 |
| 1402594 | `STR_MSG_WEAK_RACE_BUFF_DARK_MIST_OFF` | 1 |
| 1402595 | `STR_MSG_WEAK_RACE_BUFF_DARK_WARNING` | 1 |
| 1402588 | `STR_MSG_WEAK_RACE_BUFF_LIGHT_GAIN` | 1 |
| 1402589 | `STR_MSG_WEAK_RACE_BUFF_LIGHT_GET_OUT_AREA` | 1 |
| 1402590 | `STR_MSG_WEAK_RACE_BUFF_LIGHT_MIST_OFF` | 1 |
| 1402591 | `STR_MSG_WEAK_RACE_BUFF_LIGHT_WARNING` | 1 |
| 1402459 | `STR_MSG_WORLDRAID_INVADE_VRITRA` | 1 |
| 1402460 | `STR_MSG_WORLDRAID_INVADE_VRITRA_SPECIAL` | 1 |
| 1402383 | `STR_MSG_WORLDRAID_MESSAGE_01` | 1 |
| 1402384 | `STR_MSG_WORLDRAID_MESSAGE_02` | 1 |
| 1402385 | `STR_MSG_WORLDRAID_MESSAGE_03` | 1 |
| 1402386 | `STR_MSG_WORLDRAID_MESSAGE_04` | 1 |
| 1402397 | `STR_REGISTER_ITEM_MSG_UPGRADE_CANNOT` | 1 |
| 1402571 | `STR_REGISTER_ITEM_MSG_UPGRADE_CANNOT_NEED_AP` | 1 |
| 1402572 | `STR_REGISTER_ITEM_MSG_UPGRADE_CANNOT_NEED_QINA` | 1 |
| 1402421 | `STR_REGISTER_ITEM_MSG_UPGRADE_CANNOT_NO_IDENTIFY` | 1 |
| 1402918 | `STR_SKILL_NOT_NEED_PET` | 2 |
| 901713 | `STR_TOOLTIP_LEARNED_EMOTION` | 1 |
| 901714 | `STR_TOOLTIP_LEARNED_TITLE` | 2 |

Também existem **59 factories usadas cujo ID existe, mas o nome oficial associado ao número é diferente**. Elas permanecem no JSON para revisão de parâmetros.

O outro emissor ativo relacionado ao combate, `STR_MSG_BREAK_PROC` (`1402237`), só é alcançado pelos **12 Godstones de teste** com `breakprob` no servidor. **12 deles existem nos arquivos de itens do cliente oficial**; portanto, esse caminho legado não explica o uso de Skills/itens oficiais normais.

## Defesa e resistência

Os itens abaixo são caminhos de bypass encontrados no código e nos templates. A presença na lista não prova erro: efeitos de dano fixo, efeitos benéficos e certos danos atrasados podem legitimamente contornar uma camada defensiva.

| Motivo técnico | Efeitos | Skills únicas |
|---|---:|---:|
| `CANNOTMISS_XML` | 32 | 32 |
| `DANO_FIXO_HARDCODE_STACK` | 3 | 3 |
| `DANO_FIXO_SEM_DEFESAS_BASE` | 38 | 38 |
| `DANO_MAGICO_SEM_ELEMENTO_USA_DEFESA_FISICA_OU_NENHUMA` | 287 | 287 |
| `IGNORA_ESCUDOS` | 31 | 31 |
| `NORESIST_FORCADO_JAVA` | 7773 | 5238 |
| `NORESIST_XML` | 9682 | 6636 |

Há **83 efeitos** em que o servidor força/declara `noresist`, mas o campo oficial correspondente é `0`. Esses são os candidatos prioritários para teste, pois a divergência é direta.
Desses, **46 efeitos** pertencem a Skills cuja relação oficial de alvo é `Enemy`; continuam pendentes porque efeitos secundários podem herdar o acerto do primeiro efeito, algo que o XML do cliente sozinho não comprova.

### Caminho defensivo normal confirmado no código

- Antes de aplicar um efeito não forçado, `EffectTemplate` testa evasão para elemento `NONE` e resistência mágica para efeitos elementais.
- Dano físico comum desconta `PHYSICAL_DEFENSE / 10`; dano mágico elemental aplica defesa elemental e depois `MAGICAL_DEFEND / 10`.
- Os ratios defensivos PvP/PvE e escudos são aplicados depois, salvo nos bypasses enumerados abaixo.
- Portanto, Skills comuns não ignoram defesa globalmente. O risco está concentrado em efeitos/flags e hardcodes específicos.

### Semântica dos motivos

- `NORESIST_XML`: o template impede esquiva/resistência do efeito.
- `NORESIST_FORCADO_JAVA`: `Effects` muda o efeito para `noresist` durante o carregamento, mesmo sem essa ordem no XML.
- `DANO_FIXO_SEM_DEFESAS_BASE`: `NoReduceSpellATKInstantEffect` pula ataque, defesa física/mágica, defesa elemental e ratios ofensivos/defensivos; mantém apenas o modificador PvP geral.
- `DANO_FIXO_HARDCODE_STACK`: o mesmo bypass é ativado por nome de stack hardcoded.
- `IGNORA_ESCUDOS`: dano atrasado chama o cálculo com `ignoreShield=true`; defesa e resistência continuam em outros estágios.
- `DANO_MAGICO_SEM_ELEMENTO_USA_DEFESA_FISICA_OU_NENHUMA`: combinação que exige revisão individual do tipo convertido.

## Limites desta evidência

O cliente prova flags e parâmetros estáticos, mas não toda a lógica exclusiva do servidor. Nenhum bypass foi removido automaticamente. O JSON contém cada Skill, efeito, posição, stack, flag do cliente e motivo técnico para validação por PCAP/teste.
