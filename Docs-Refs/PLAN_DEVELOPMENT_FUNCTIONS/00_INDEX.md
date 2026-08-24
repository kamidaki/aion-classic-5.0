# PLAN_DEVELOPMENT_FUNCTIONS — Índice Mestre

> **Plano cirúrgico de implementação baseado em capturas Wireshark do servidor oficial Gameforge Classic 4.5**
> Cada arquivo é uma unidade de execução autônoma. Executar **em ordem numérica**. Marcar como `[x]` ao concluir e fazer commit ao terminar cada MD.

---

## Regras de Execução

- Nunca inventar dados, structs ou valores. Tudo deve ser fiel ao wire capturado.
- Após concluir cada MD: `git add -A && git commit -m "PLAN-XX: <título>"`
- Testar com o client real antes de marcar como concluído.
- Opcodes, offsets e tamanhos são **obrigatoriamente** os da captura — não aproximações.

---

## Tabela de Execução

| # | Arquivo | Domínio | Status |
|---|---------|---------|--------|
| 01 | 01_ENTRADA_MUNDO_SPAWN.md | Spawn, Cutscene, S_REQUEST_TELEPORT | `[x]` |
| 02 | 02_MOVEMENT_WINDSTREAM.md | C_MOVE, S_MOVE, Windstream (0x046/0x0a2/0x0a3) | `[x]` |
| 03 | 03_COMBAT_SKILLS.md | C_USE_SKILL, S_SKILL_SUCCEDED, S_ABNORMAL_STATUS | `[x]` |
| 04 | 04_COMBAT_AUTOATTACK.md | C_ATTACK, S_ATTACK_STATUS, SM_CASTSPELL_RESULT | `[x]` |
| 05 | 05_NPC_DIALOG_QUESTS.md | SM_DIALOG_WINDOW, missões, SM_QUEST_LIST | `[x]` |
| 06 | 06_NPC_SHOP_BUYBACK.md | C_BUY_SELL, S_STORE_SALE_INFO, S_USER_SELL_HISTORY_LIST | `[x]` |
| 07 | 07_INVENTORY_ITEMS.md | SM_INVENTORY_INFO, equip/desequip, SM_UPDATE_PLAYER_APPEARANCE | `[x]` |
| 08 | 08_MAIL_SYSTEM.md | C_MAIL_READ, C_MAIL_POSTMAN, S_MAIL (0x0a0) | `[x]` |
| 09 | 09_LEGION_GUILD.md | S_GUILD_INFO, S_GUILD_MEMBER_INFO, emblemas, buffs | `[x]` |
| 10 | 10_SOCIAL_PARTY_BUDDY.md | C_PARTY, C_ADD_BUDDY, S_BUDDY_LIST, S_ALLIANCE_INFO | `[x]` |
| 11 | 11_TRADE_BROKER.md | S_GLOBAL_TRADE_LIST, S_GLOBAL_TRADE_SALESLOG, S_GLOBAL_TRADE_STATE | `[x]` |
| 12 | 12_CHAT_CHANNELS.md | SM_MESSAGE, whisper, canais regionais, anti-flood | `[x]` |
| 13 | 13_DATABASE_SCHEMA.md | SQLite: players expandido, quests, mail, legion, inventory | `[x]` |
| 14 | 14_CHARACTER_CREATION.md | CM_CREATE_CHARACTER completo, kit inicial, skills iniciais | `[ ]` |
| 15 | 15_WORLD_TELEPORT.md | S_REQUEST_TELEPORT (22 bytes), troca de mapa, instâncias | `[ ]` |
