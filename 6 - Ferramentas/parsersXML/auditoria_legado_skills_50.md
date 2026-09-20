# Auditoria detalhada das skills Classic 5.0

Esta auditoria não altera os dados. Divergência em relação ao cliente não prova, sozinha, origem na 4.8. Aliases e regras do servidor exigem confirmação semântica.

## Escopo e conclusão

Foram comparadas 12114 definições oficiais com 12139 templates do servidor, 3969 IDs presentes na árvore de jogadores e 31523 registros de aprendizado. Também foram examinados o registro JAXB, implementações de efeitos Java e os geradores XML.

A migração anterior não encerrou a compatibilidade 5.0. Ainda há efeitos oficiais ausentes, conversões sem equivalência e implementações incompletas. Os 62 casos estruturais do relatório anterior não eram o total de pendências. As categorias abaixo se sobrepõem: seus totais não devem ser somados.

## Estado das correções

- As funções ADD/PERCENT, incluindo a passiva 2750 do Brawler, estão sincronizadas com os pares explícitos R2/R4 e flags R6/R7 do cliente.
- As restrições de armas e a permissão de movimento das skills presentes na árvore de jogadores estão sincronizadas. Divergências de arma remanescentes pertencem a NPCs; WeaponCondition não as valida para NPCs.
- As skills 724, 2088, 2189 e 2206 receberam o DispelDebuffPhysical oficial que estava ausente.
- **4448 e outras seis passivas do Soul Reaper:** o segundo efeito agora usa StatSynergy com fonte, destino e razão oficiais; o motor recalcula o bônus a partir do atributo atual.
- **Blending do Soul Reaper:** seis passivas combinadas são concedidas e removidas pelas combinações oficiais de aprendizado. As cinco graduações de Blade Assault agora compartilham o contador oficial e disparam a skill combinada no segundo acúmulo.
- **2521–2523 — Utility:** os templates usam uma classe cujo applyEffect está vazio. Registro JAXB e XML válido não garantem execução do efeito.

## Riscos nos geradores e na atualização anterior

- build_50_player_skill_effects.py não gera mais PHYSICAL_ATTACK/ADD/10, NPC 200000, duração ou valor genérico para efeitos desconhecidos. Tipos não traduzidos permanecem como pendência.
- rebuild_50_skill_effects.py aprende correspondências a partir dos templates 4.8 por frequência estatística. Uma correspondência frequente não prova equivalência para todos os tipos e parâmetros 5.0.
- refresh_50_skills.py preserva atributos sem fonte explícita para não apagar comportamento ainda não compreendido. ADD/PERCENT e as flags R6/R7 já são tratadas separadamente.
- ShapeChange e Polymorph têm classes Java distintas; Polymorph altera também a tribo do NPC. O alias usado na atualização anterior não demonstra equivalência de comportamento.

## Como interpretar os números

Ausência de efeito e diferença de campo explícito são evidências diretas. Conversão de tipo, atributo sem fonte, motion e política de aprendizado exigem revisão semântica. A divergência de nameId inclui IDs ausentes e IDs diferentes; não mede a qualidade da tradução textual.

| Achado | Ocorrências | Skills | Skills de jogadores |
|---|---:|---:|---:|
| definicao_cliente_sem_template | 1 | 1 | 0 |
| template_sem_definicao_cliente | 26 | 26 | 0 |
| efeito_oficial_ausente | 987 | 552 | 0 |
| motion_divergente | 972 | 972 | 588 |
| atributo_preservado_sem_fonte | 60 | 50 | 31 |
| restricao_arma_sem_fonte | 301 | 301 | 281 |
| corrente_divergente | 44 | 19 | 0 |
| tipo_efeito_sem_equivalencia | 79 | 69 | 0 |
| preefeito_sem_condicao_cliente | 12 | 12 | 4 |
| restricao_arma_divergente | 4878 | 4878 | 0 |
| efeito_sem_slot_oficial | 6 | 6 | 0 |
| posicao_efeito_duplicada | 1 | 1 | 0 |
| arvore_divergente | 916 | 33 | 33 |

Classes Java com implementação vazia: 8.

A árvore foi comparada usando a tradução de classes do gerador atual; esta comparação não valida a própria tradução.
A comparação de motions mede nomes e disponibilidade em motion_times.xml; não comprova, sozinha, animação incorreta no cliente. Os 26 templates sem definição oficial não aparecem na árvore de jogadores, e a busca por atributos skill_id/skillId/skillid não encontrou referências a eles nos demais XMLs; isso não basta para autorizar sua remoção.

## Ordem recomendada para correção

1. Remover dos geradores as substituições e valores inventados; tipos desconhecidos devem produzir pendência identificada.
2. Corrigir funções de atributos, contribuições de StatBoost, restrições e efeitos ausentes com tradução confirmada; preservar efeitos ainda não compreendidos.
3. Implementar os efeitos 5.0 especiais no motor, começando por StatSynergy e Blending de Soul Reaper; corrigir Utility e resolver Control/FlyBoost/RadarAngle.
4. Revisar motion_times, identificadores de texto e política de aprendizado. Validar por classe e tipo de efeito em combate, comparando com capturas oficiais quando disponíveis.

## Limites da validação

Esta etapa é uma análise estática. Não houve teste de combate nem demonstração de equivalência com Game.dll. A classificação de skills de jogadores segue a árvore atual do servidor. Nenhum template, Java ou binário foi alterado pela execução deste auditor.

## Exemplos por categoria

### definicao_cliente_sem_template

- `50068` / `action_pet_pc_doping3`: `template` servidor `None`; cliente `action_pet_pc_doping3`. divergência direta.

### template_sem_definicao_cliente

- `418` / `kn_grandprotection_g2`: `template` servidor `KN_GRANDPROTECTION_G2`; cliente `None`. ausência confirmada; origem histórica a confirmar.
- `459` / `kn_avengingblade_g4`: `template` servidor `KN_AVENGINGBLADE_G4`; cliente `None`. ausência confirmada; origem histórica a confirmar.
- `460` / `kn_grandprotection_g3`: `template` servidor `KN_GRANDPROTECTION_G3`; cliente `None`. ausência confirmada; origem histórica a confirmar.
- `854` / `as_hellsblade_g3`: `template` servidor `AS_HELLSBLADE_G3`; cliente `None`. ausência confirmada; origem histórica a confirmar.
- `993` / `cl_soniceruption_g5`: `template` servidor `CL_SONICERUPTION_G5`; cliente `None`. ausência confirmada; origem histórica a confirmar.

### efeito_oficial_ausente

- `203` / `Enchant_Effect_COMBINE_60_ProcDamageReduce`: `effect1` servidor `None`; cliente `Statup`. divergência direta.
- `203` / `Enchant_Effect_COMBINE_60_ProcDamageReduce`: `effect2` servidor `None`; cliente `DRBoost`. divergência direta.
- `204` / `Enchant_Effect_COMBINE_65_4CCDuration`: `effect1` servidor `None`; cliente `Statup`. divergência direta.
- `204` / `Enchant_Effect_COMBINE_65_4CCDuration`: `effect2` servidor `None`; cliente `Statup`. divergência direta.
- `205` / `Enchant_Effect_COMBINE_75_4CCDuration`: `effect1` servidor `None`; cliente `Statup`. divergência direta.

### motion_divergente

- `621` / `RA_Light_BlazingTrap_G1`: `motion` servidor `ThrowTrap`; cliente `TrapFire`. motion oficial disponível no servidor.
- `622` / `RA_Dark_BlazingTrap_G1`: `motion` servidor `ThrowTrap`; cliente `TrapFire`. motion oficial disponível no servidor.
- `623` / `RA_Light_BlazingTrap_G2`: `motion` servidor `ThrowTrap`; cliente `TrapFire`. motion oficial disponível no servidor.
- `624` / `RA_Dark_BlazingTrap_G2`: `motion` servidor `ThrowTrap`; cliente `TrapFire`. motion oficial disponível no servidor.
- `633` / `RA_Light_ThrowingTrap_G1`: `motion` servidor `PhBurst2`; cliente `TrapFire`. motion oficial disponível no servidor.

### atributo_preservado_sem_fonte

- `646` / `RA_Stigma_TigerEye_G1`: `effect1_duration2` servidor `60000`; cliente `None`. resíduo possível; ausência não prova erro.
- `646` / `RA_Stigma_TigerEye_G1`: `effect2_duration2` servidor `60000`; cliente `None`. resíduo possível; ausência não prova erro.
- `646` / `RA_Stigma_TigerEye_G1`: `effect3_duration2` servidor `60000`; cliente `None`. resíduo possível; ausência não prova erro.
- `813` / `AS_ClearFocus_G1`: `effect1_duration2` servidor `60000`; cliente `None`. resíduo possível; ausência não prova erro.
- `829` / `AS_PoisoningIntention_G1`: `effect1_duration2` servidor `120000`; cliente `None`. resíduo possível; ausência não prova erro.

### restricao_arma_sem_fonte

- `829` / `AS_PoisoningIntention_G1`: `weapon` servidor `['DAGGER', 'GREATSWORD', 'MACE', 'POLEARM', 'STAFF', 'SWORD']`; cliente `None`. restrição residual; conferir campos novos.
- `830` / `AS_PoisoningIntention_G2`: `weapon` servidor `['DAGGER', 'GREATSWORD', 'MACE', 'POLEARM', 'STAFF', 'SWORD']`; cliente `None`. restrição residual; conferir campos novos.
- `831` / `AS_PoisoningIntention_G3`: `weapon` servidor `['DAGGER', 'GREATSWORD', 'MACE', 'POLEARM', 'STAFF', 'SWORD']`; cliente `None`. restrição residual; conferir campos novos.
- `862` / `AS_PoisoningIntention_G4`: `weapon` servidor `['DAGGER', 'GREATSWORD', 'MACE', 'POLEARM', 'STAFF', 'SWORD']`; cliente `None`. restrição residual; conferir campos novos.
- `919` / `AS_StuningIntention_G1`: `weapon` servidor `['DAGGER', 'GREATSWORD', 'MACE', 'POLEARM', 'STAFF', 'SWORD']`; cliente `None`. restrição residual; conferir campos novos.

### corrente_divergente

- `1629` / `EL_Dispel_G2`: `chain.category` servidor `None`; cliente `MWE_CHAINL_1TH`. divergência direta.
- `1629` / `EL_Dispel_G2`: `chain.time` servidor `None`; cliente `5000`. divergência direta.
- `1630` / `EL_Dispel_G3`: `chain.category` servidor `None`; cliente `MWE_CHAINL_1TH`. divergência direta.
- `1630` / `EL_Dispel_G3`: `chain.time` servidor `None`; cliente `5000`. divergência direta.
- `1704` / `EL_Dispel_G4`: `chain.category` servidor `None`; cliente `MWE_CHAINL_1TH`. divergência direta.

### tipo_efeito_sem_equivalencia

- `1863` / `Q_Polymorph_Lehpar`: `effect1_type` servidor `shapechange`; cliente `Polymorph`. conversão exige revisão semântica.
- `1865` / `Q_Polymorph_LehparM`: `effect1_type` servidor `shapechange`; cliente `Polymorph`. conversão exige revisão semântica.
- `1868` / `Q_Lycan_Polymorph_M`: `effect1_type` servidor `shapechange`; cliente `Polymorph`. conversão exige revisão semântica.
- `2252` / `Q_Polymorph_Drakan`: `effect1_type` servidor `shapechange`; cliente `Polymorph`. conversão exige revisão semântica.
- `8197` / `Polymorph_Parrot`: `effect1_type` servidor `shapechange`; cliente `Polymorph`. conversão exige revisão semântica.

### preefeito_sem_condicao_cliente

- `2526` / `KN_DefendShield_G1`: `effect1_preeffect` servidor `1`; cliente `None`. resíduo possível.
- `3054` / `KN_DefendShield_G2`: `effect1_preeffect` servidor `1`; cliente `None`. resíduo possível.
- `11540` / `Classic_S_PhyCriAcc_shoulder_G2`: `effect1_preeffect` servidor `1`; cliente `None`. resíduo possível.
- `11568` / `Classic_S_HPBlkHealBoost_torso_G2`: `effect1_preeffect` servidor `1`; cliente `None`. resíduo possível.
- `18481` / `BNMA_Shield_HolyServant`: `effect1_preeffect` servidor `2`; cliente `None`. resíduo possível.

### restricao_arma_divergente

- `8193` / `Item_ReturnHome`: `weapon` servidor `['BOW', 'CHAINBLADE', 'DAGGER', 'DIMENSIONSWORD', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'RUNESWORD', 'SPELLBOOK', 'STAFF', 'SWORD']`; cliente `['BOW', 'CHAINBLADE', 'DAGGER', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'SPELLBOOK', 'STAFF', 'SWORD']`. divergência direta.
- `8194` / `ACTIVATE_ENSLAVE`: `weapon` servidor `['BOW', 'CHAINBLADE', 'DAGGER', 'DIMENSIONSWORD', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'RUNESWORD', 'SPELLBOOK', 'STAFF', 'SWORD']`; cliente `['BOW', 'CHAINBLADE', 'DAGGER', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'SPELLBOOK', 'STAFF', 'SWORD']`. divergência direta.
- `8195` / `Polymorph_Orc`: `weapon` servidor `['BOW', 'CHAINBLADE', 'DAGGER', 'DIMENSIONSWORD', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'RUNESWORD', 'SPELLBOOK', 'STAFF', 'SWORD']`; cliente `['BOW', 'CHAINBLADE', 'DAGGER', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'SPELLBOOK', 'STAFF', 'SWORD']`. divergência direta.
- `8196` / `Dispel_Polymorph`: `weapon` servidor `['BOW', 'CHAINBLADE', 'DAGGER', 'DIMENSIONSWORD', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'RUNESWORD', 'SPELLBOOK', 'STAFF', 'SWORD']`; cliente `['BOW', 'CHAINBLADE', 'DAGGER', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'SPELLBOOK', 'STAFF', 'SWORD']`. divergência direta.
- `8198` / `Item_ReturnPoint`: `weapon` servidor `['BOW', 'CHAINBLADE', 'DAGGER', 'DIMENSIONSWORD', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'RUNESWORD', 'SPELLBOOK', 'STAFF', 'SWORD']`; cliente `['BOW', 'CHAINBLADE', 'DAGGER', 'GAUNTLET', 'GREATSWORD', 'GUN', 'MACE', 'ORB', 'POLEARM', 'SPELLBOOK', 'STAFF', 'SWORD']`. divergência direta.

### efeito_sem_slot_oficial

- `16953` / `Test_Flying_DelayDD`: `effect2` servidor `['hostileup']`; cliente `None`. estrutura residual; equivalência funcional a confirmar.
- `19512` / `IDElemental_Prime_Buff4`: `effect2` servidor `['statdown']`; cliente `None`. estrutura residual; equivalência funcional a confirmar.
- `19513` / `IDElemental_Prime_Buff5`: `effect2` servidor `['statdown']`; cliente `None`. estrutura residual; equivalência funcional a confirmar.
- `19514` / `IDElemental_Prime_Buff6`: `effect2` servidor `['statdown']`; cliente `None`. estrutura residual; equivalência funcional a confirmar.
- `19515` / `IDElemental_Prime_Buff7`: `effect2` servidor `['statdown']`; cliente `None`. estrutura residual; equivalência funcional a confirmar.

### posicao_efeito_duplicada

- `16959` / `Test_GB_Stance0_MO`: `effect1` servidor `2`; cliente `1`. divergência direta.

### arvore_divergente

- `2805` / `ST_upper_high_G1`: `('BRAWLER', '2805', '5', 'PC_ALL').autoLearn` servidor `true`; cliente `false`. segundo tradução de classes do gerador atual.
- `2805` / `ST_upper_high_G1`: `('BRAWLER', '2805', '5', 'PC_ALL').skillBook` servidor `None`; cliente `true`. segundo tradução de classes do gerador atual.
- `2805` / `ST_upper_high_G1`: `('BRAWLER', '2805', '6', 'PC_ALL').autoLearn` servidor `true`; cliente `false`. segundo tradução de classes do gerador atual.
- `2805` / `ST_upper_high_G1`: `('BRAWLER', '2805', '6', 'PC_ALL').skillBook` servidor `None`; cliente `true`. segundo tradução de classes do gerador atual.
- `2805` / `ST_upper_high_G1`: `('BRAWLER', '2805', '7', 'PC_ALL').autoLearn` servidor `true`; cliente `false`. segundo tradução de classes do gerador atual.

## Evidência completa

IDs, classes, campos e valores estão em `auditoria_legado_skills_50.json`.
