# Lista Completa dos 321 Opcodes de Servidor (SM_*) — Aion Classic 5.0

Mapeamento extraído diretamente de `ServerPacketsOpcodes.java` e cruzado com o código-fonte do GameServer:

- **Total de Opcodes Registrados:** 321
- **Ativos (instanciados e enviados ativamente):** 280
- **Mapeados (registrados no protocolo, sem envio ativo):** 41

| Dec | Hex | Classe Java (Emulador) | Nome Oficial / Descrição | Status no Emulador |
|:---:|:---:|:---|:---|:---:|
| 0 | `0x0000` | `SM_VERSION_CHECK` | [S_VERSION_CHECK] | Ativo |
| 1 | `0x0001` | `SM_STATS_INFO` | [S_STATUS] | Ativo |
| 2 | `0x0002` | `SM_GM_SHOW_PLAYER_STATUS` | [S_STATUS_OTHER] | Mapeado (Não instanciado) |
| 3 | `0x0003` | `SM_STATUPDATE_HP` | [S_HIT_POINT] | Ativo |
| 4 | `0x0004` | `SM_STATUPDATE_MP` | [S_MANA_POINT] | Ativo |
| 5 | `0x0005` | `SM_ATTACK_STATUS` | [S_HIT_POINT_OTHER] | Ativo |
| 6 | `0x0006` | `SM_STATUPDATE_DP` | [S_DP] | Ativo |
| 7 | `0x0007` | `SM_DP_INFO` | [S_DP_USER] | Ativo |
| 8 | `0x0008` | `SM_STATUPDATE_EXP` | [S_EXP] | Ativo |
| 10 | `0x000A` | `SM_NPC_ASSEMBLER` | [S_CUTSCENE_NPC_INFO] | Ativo |
| 11 | `0x000B` | `SM_LEGION_UPDATE_NICKNAME` | [S_CHANGE_GUILD_MEMBER_NICKNAME] | Ativo |
| 12 | `0x000C` | `SM_LEGION_HISTORY` | [S_GUILD_HISTORY] | Ativo |
| 13 | `0x000D` | `SM_TUTORIAL_HINT` | [S_TUTORIAL_HINT] 5.0 Classic | Ativo |
| 14 | `0x000E` | `SM_NPC_INFO` | [S_PUT_NPC] | Ativo |
| 15 | `0x000F` | `SM_PLAYER_SPAWN` | [S_WORLD] | Ativo |
| 17 | `0x0011` | `SM_GATHERABLE_INFO` | [S_PUT_OBJECT] | Ativo |
| 19 | `0x0013` | `SM_GM_SEARCH` | [S_BUILDER_RESULT] | Mapeado (Não instanciado) |
| 20 | `0x0014` | `SM_TELEPORT_LOC` | [S_REQUEST_TELEPORT] | Ativo |
| 21 | `0x0015` | `SM_POSITION_SELF` | [S_BLINK] | Mapeado (Não instanciado) |
| 22 | `0x0016` | `SM_DELETE` | [S_REMOVE_OBJECT] | Ativo |
| 23 | `0x0017` | `SM_LOGIN_QUEUE` | [S_WAIT_LIST] | Mapeado (Não instanciado) |
| 24 | `0x0018` | `SM_MESSAGE` | [S_MESSAGE] | Ativo |
| 25 | `0x0019` | `SM_SYSTEM_MESSAGE` | [S_MESSAGE_CODE] | Ativo |
| 26 | `0x001A` | `SM_INVENTORY_INFO` | [S_LOAD_INVENTORY] | Ativo |
| 27 | `0x001B` | `SM_INVENTORY_ADD_ITEM` | [S_ADD_INVENTORY] | Ativo |
| 28 | `0x001C` | `SM_DELETE_ITEM` | [S_REMOVE_INVENTORY] | Ativo |
| 29 | `0x001D` | `SM_INVENTORY_UPDATE_ITEM` | [S_CHANGE_ITEM_DESC] | Ativo |
| 30 | `0x001E` | `SM_UI_SETTINGS` | [S_LOAD_CLIENT_SETTINGS] | Ativo |
| 31 | `0x001F` | `SM_PLAYER_STANCE` | [S_CHANGE_STANCE] | Ativo |
| 32 | `0x0020` | `SM_PLAYER_INFO` | [S_PUT_USER] | Ativo |
| 33 | `0x0021` | `SM_CASTSPELL` | [S_USE_SKILL] | Ativo |
| 34 | `0x0022` | `SM_GATHER_ANIMATION` | [S_GATHER_OTHER] | Ativo |
| 35 | `0x0023` | `SM_GATHER_UPDATE` | [S_GATHER] | Ativo |
| 36 | `0x0024` | `SM_UPDATE_PLAYER_APPEARANCE` | [S_WIELD] | Ativo |
| 37 | `0x0025` | `SM_EMOTION` | [S_ACTION] | Ativo |
| 38 | `0x0026` | `SM_GAME_TIME` | [S_TIME] | Ativo |
| 39 | `0x0027` | `SM_TIME_CHECK` | [S_SYNC_TIME] | Ativo |
| 40 | `0x0028` | `SM_LOOKATOBJECT` | [S_NPC_CHANGED_TARGET] | Ativo |
| 41 | `0x0029` | `SM_TARGET_SELECTED` | [S_TARGET_INFO] | Ativo |
| 42 | `0x002A` | `SM_SKILL_CANCEL` | [S_SKILL_CANCELED] | Ativo |
| 43 | `0x002B` | `SM_CASTSPELL_RESULT` | [S_SKILL_SUCCEDED] | Ativo |
| 44 | `0x002C` | `SM_SKILL_LIST` | [S_ADD_SKILL] | Ativo |
| 45 | `0x002D` | `SM_SKILL_REMOVE` | [S_DELETE_SKILL] | Ativo |
| 46 | `0x002E` | `SM_SKILL_ACTIVATION` | [S_TOGGLE_SKILL_ON_OFF] | Ativo |
| 49 | `0x0031` | `SM_ABNORMAL_STATE` | [S_ABNORMAL_STATUS] | Ativo |
| 50 | `0x0032` | `SM_ABNORMAL_EFFECT` | [S_ABNORMAL_STATUS_OTHER] | Ativo |
| 51 | `0x0033` | `SM_SKILL_COOLDOWN` | [S_LOAD_SKILL_COOLTIME] | Ativo |
| 52 | `0x0034` | `SM_QUESTION_WINDOW` | [S_ASK] | Ativo |
| 53 | `0x0035` | `SM_CLOSE_QUESTION_WINDOW` | [S_CANCEL_ASK] | Ativo |
| 54 | `0x0036` | `SM_ATTACK` | [S_ATTACK] | Ativo |
| 55 | `0x0037` | `SM_MOVE` | [S_MOVE_NEW] | Ativo |
| 57 | `0x0039` | `SM_HEADING_UPDATE` | [S_CHANGE_DIRECTION] | Ativo |
| 58 | `0x003A` | `SM_TRANSFORM` | [S_POLYMORPH] | Ativo |
| 59 | `0x003B` | `SM_GM_SHOW_PLAYER_SKILLS` | [S_SKILL_OTHER] | Mapeado (Não instanciado) |
| 60 | `0x003C` | `SM_DIALOG_WINDOW` | [S_NPC_HTML_MESSAGE] | Ativo |
| 64 | `0x0040` | `SM_VIEW_PLAYER_DETAILS` | [S_ITEM_LIST] (0x40, was 65) | Ativo |
| 66 | `0x0042` | `SM_WEATHER` | [S_WEATHER] (0x42, was 67) | Ativo |
| 67 | `0x0043` | `SM_PLAYER_STATE` | [S_INVISIBLE_LEVEL] (0x43, was 68) | Ativo |
| 68 | `0x0044` | `SM_RECALLED_BY_OTHER` | [S_RECALLED_BY_OTHER] (0x44, was 69) | Ativo |
| 69 | `0x0045` | `SM_ACTION_ANIMATION` | [S_EFFECT] (0x45, was 70) | Ativo |
| 70 | `0x0046` | `SM_QUEST_LIST` | [S_LOAD_WORKINGQUEST] (0x46, was 71) | Ativo |
| 71 | `0x0047` | `SM_KEY` | [S_KEY] (0x47, was 72) | Ativo |
| 72 | `0x0048` | `SM_SUMMON_PANEL_REMOVE` | [S_RESET_SKILL_COOLING_TIME] (0x48, was 73) | Ativo |
| 73 | `0x0049` | `SM_EXCHANGE_REQUEST` | [S_XCHG_START] (0x49, was 74) | Ativo |
| 74 | `0x004A` | `SM_EXCHANGE_ADD_ITEM` | [S_ADD_XCHG] (0x4A, was 75) | Ativo |
| 76 | `0x004C` | `SM_EXCHANGE_ADD_KINAH` | [S_XCHG_GOLD] (0x4C, was 77) | Ativo |
| 77 | `0x004D` | `SM_EXCHANGE_CONFIRMATION` | [S_XCHG_RESULT] (0x4D, was 78) | Ativo |
| 78 | `0x004E` | `SM_EMOTION_LIST` | [S_ADDREMOVE_SOCIAL] (0x4E, was 79) | Ativo |
| 80 | `0x0050` | `SM_TARGET_UPDATE` | [S_USER_CHANGED_TARGET] (0x50, was 81) | Ativo |
| 82 | `0x0052` | `SM_PLASTIC_SURGERY` | [S_EDIT_CHARACTER] (0x52, was 83) | Ativo |
| 83 | `0x0053` | `SM_CONQUEROR_PROTECTOR` | [S_SERIAL_KILLER_LIST] (0x53, was 84) | Mapeado (Não instanciado) |
| 84 | `0x0054` | `SM_INFLUENCE_RATIO` | [S_ABYSS_NEXT_PVP_CHANGE_TIME] (0x54, was 85) | Ativo |
| 85 | `0x0055` | `SM_FORTRESS_STATUS` | [S_ABYSS_CHANGE_NEXT_PVP_STATUS] (0x55, was 86) | Ativo |
| 86 | `0x0056` | `SM_CAPTCHA` | [S_CAPTCHA] (0x56, was 87) | Ativo |
| 87 | `0x0057` | `SM_RENAME` | [S_ADDED_SERVICE_CHANGE] (0x57, was 88) | Ativo |
| 88 | `0x0058` | `SM_SHOW_NPC_ON_MAP` | [S_FIND_NPC_POS_RESULT] (0x58, was 89) | Ativo |
| 89 | `0x0059` | `SM_GROUP_INFO` | [S_PARTY_INFO] (0x59, was 90) | Ativo |
| 90 | `0x005A` | `SM_GROUP_MEMBER_INFO` | [S_PARTY_MEMBER_INFO] (0x5A, was 91) | Ativo |
| 95 | `0x005F` | `SM_SPECIAL_CURRENCY_SLOTS` | [S_SPECIAL_CURRENCY_SLOTS] (0x005F) | Mapeado (Não instanciado) |
| 97 | `0x0061` | `SM_QUIT_RESPONSE` | [S_ASK_QUIT_RESULT] (0x61, was 98) | Ativo |
| 98 | `0x0062` | `SM_CHAT_WINDOW` | [S_ASK_INFO_RESULT] (0x62, was 99) | Ativo |
| 100 | `0x0064` | `SM_PET` | [S_FUNCTIONAL_PET] (0x64, was 101) | Ativo |
| 102 | `0x0066` | `SM_ITEM_COOLDOWN` | [S_LOAD_ITEM_COOLTIME] (0x66, was 103) | Ativo |
| 103 | `0x0067` | `SM_UPDATE_NOTE` | [S_TODAY_WORDS] (0x67, was 104) | Ativo |
| 104 | `0x0068` | `SM_PLAY_MOVIE` | [S_PLAY_CUTSCENE] (0x68, was 105) | Ativo |
| 109 | `0x006D` | `SM_LEGION_INFO` | [S_GUILD_INFO] (0x6D, was 110) | Ativo |
| 110 | `0x006E` | `SM_LEGION_ADD_MEMBER` | [S_ADD_GUILD_MEMBER] (0x6E, was 111) | Ativo |
| 111 | `0x006F` | `SM_LEGION_LEAVE_MEMBER` | [S_DELETE_GUILD_MEMBER] (0x6F, was 112) | Ativo |
| 112 | `0x0070` | `SM_LEGION_UPDATE_MEMBER` | [S_CHANGE_GUILD_MEMBER_INFO] (0x70, was 113) | Ativo |
| 113 | `0x0071` | `SM_LEGION_UPDATE_TITLE` | [S_CHANGE_GUILD_OTHER] (0x71, was 114) | Ativo |
| 114 | `0x0072` | `SM_ATTACK_RESPONSE` | [S_ATTACK_RESULT] (0x72, was 115) | Ativo |
| 118 | `0x0076` | `SM_LEGION_UPDATE_SELF_INTRO` | [S_CHANGE_GUILD_MEMBER_INTRO] (0x76, was 119) | Ativo |
| 120 | `0x0078` | `SM_INSTANCE_SCORE` | [S_INSTANT_DUNGEON_INFO] (0x78, was 121) | Ativo |
| 121 | `0x0079` | `SM_AUTO_GROUP` | [S_MATCHMAKER_INFO] (0x79, was 122) | Ativo |
| 122 | `0x007A` | `SM_QUEST_COMPLETED_LIST` | [S_LOAD_FINISHEDQUEST] (0x7A, was 123) | Ativo |
| 123 | `0x007B` | `SM_QUEST_ACTION` | [S_QUEST] (0x7B, was 124) | Ativo |
| 126 | `0x007E` | `SM_NEARBY_QUESTS` | [S_UPDATE_ZONE_QUEST] (0x7E, was 127) | Ativo |
| 127 | `0x007F` | `SM_PING_RESPONSE` | [S_PING] (0x7F, was 128) | Mapeado (Não instanciado) |
| 129 | `0x0081` | `SM_CUBE_UPDATE` | [S_EVENT] (0x81, was 130) | Ativo |
| 131 | `0x0083` | `SM_FRIEND_LIST` | [S_BUDDY_LIST] (0x83, was 132) | Ativo |
| 133 | `0x0085` | `SM_PRIVATE_STORE` | [S_SHOP_SELL_LIST] (0x85, was 134) | Ativo |
| 134 | `0x0086` | `SM_GROUP_LOOT` | [S_GROUP_ITEM_DIST] (0x86, was 135) | Ativo |
| 135 | `0x0087` | `SM_ABYSS_RANK_UPDATE` | [S_ETC_STATUS] (0x87, was 136) | Ativo |
| 136 | `0x0088` | `SM_MAY_LOGIN_INTO_GAME` | [S_SA_ACCOUNT_ITEM_NOTI] (0x88, was 137) | Ativo |
| 137 | `0x0089` | `SM_ABYSS_RANKING_PLAYERS` | [S_ABYSS_RANKER_INFOS] (0x89, was 138) | Ativo |
| 138 | `0x008A` | `SM_ABYSS_RANKING_LEGIONS` | [S_ABYSS_GUILD_INFOS] (0x8A, was 139) | Ativo |
| 139 | `0x008B` | `SM_WORLD_SCENE_STATUS` | [S_WORLD_SCENE_STATUS] (0x8B) | Ativo |
| 140 | `0x008C` | `SM_INSTANCE_INFO` | [S_INSTANCE_DUNGEON_COOLTIMES] (0x8C, was 141) | Ativo |
| 141 | `0x008D` | `SM_PONG` | [S_ALIVE] (0x8D, was 142) | Ativo |
| 143 | `0x008F` | `SM_KISK_UPDATE` | [S_PLACEABLE_BINDSTONE_INFO] (0x8F, was 144) | Ativo |
| 144 | `0x0090` | `SM_PRIVATE_STORE_NAME` | [S_PERSONAL_SHOP] (0x90, was 145) | Ativo |
| 145 | `0x0091` | `SM_BROKER_SERVICE` | [S_VENDOR] (0x91, was 146) | Ativo |
| 146 | `0x0092` | `SM_ENTER_WORLD_NOTIFY` | [S_ENTER_WORLD_NOTIFY] (0x0092) | Mapeado (Não instanciado) |
| 147 | `0x0093` | `SM_MOTION` | [S_CUSTOM_ANIM] (0x93, was 148) | Ativo |
| 150 | `0x0096` | `SM_TRADE_IN_LIST` | [S_TRADE_IN] (0x96) | Ativo |
| 152 | `0x0098` | `SM_SUMMON_PANEL` | [S_ADD_PET] (0x98) | Ativo |
| 153 | `0x0099` | `SM_SUMMON_OWNER_REMOVE` | [S_REMOVE_PET] (0x99) | Ativo |
| 154 | `0x009A` | `SM_SUMMON_UPDATE` | [S_CHANGE_PET_STATUS] (0x9A) | Ativo |
| 155 | `0x009B` | `SM_TRANSFORM_IN_SUMMON` | [S_CHANGE_MASTER] (0x9B) | Mapeado (Não instanciado) |
| 156 | `0x009C` | `SM_LEGION_MEMBERLIST` | [S_GUILD_MEMBER_INFO] (0x9C) | Ativo |
| 157 | `0x009D` | `SM_LEGION_EDIT` | [S_CHANGE_GUILD_INFO] (0x9D) | Ativo |
| 160 | `0x00A0` | `SM_MAIL_SERVICE` | [S_MAIL] (0xA0, was 161) | Ativo |
| 161 | `0x00A1` | `SM_SUMMON_USESKILL` | [S_ALLOW_PET_USE_SKILL] (0xA1, was 162) | Ativo |
| 162 | `0x00A2` | `SM_WINDSTREAM` | [S_WIND_PATH_RESULT] (0xA2, was 163) | Ativo |
| 163 | `0x00A3` | `SM_WINDSTREAM_ANNOUNCE` | [S_WIND_STATE_INFO] (0xA3, was 164) | Ativo |
| 164 | `0x00A4` | `SM_RECIPE_COOLDOWN` | [S_LOAD_GATHERCOMBINE_COOLTIME] (0xA4, was 165) | Mapeado (Não instanciado) |
| 165 | `0x00A5` | `SM_FIND_GROUP` | [S_PARTY_MATCH] (0xA5, was 166) | Ativo |
| 166 | `0x00A6` | `SM_REPURCHASE` | [S_USER_SELL_HISTORY_LIST] (0xA6, was 167) | Ativo |
| 167 | `0x00A7` | `SM_WAREHOUSE_INFO` | [S_LOAD_WAREHOUSE] (0xA7, was 168) | Ativo |
| 168 | `0x00A8` | `SM_WAREHOUSE_ADD_ITEM` | [S_ADD_WAREHOUSE] (0xA8, was 169) | Ativo |
| 169 | `0x00A9` | `SM_DELETE_WAREHOUSE_ITEM` | [S_REMOVE_WAREHOUSE] (0xA9, was 170) | Ativo |
| 170 | `0x00AA` | `SM_WAREHOUSE_UPDATE_ITEM` | [S_CHANGE_WAREHOUSE_ITEM_DESC] (0xAA, was 171) | Ativo |
| 175 | `0x00AF` | `SM_TITLE_INFO` | [S_TITLE] (0xAF, was 176) | Ativo |
| 176 | `0x00B0` | `SM_CHARACTER_SELECT` | [S_2ND_PASSWORD] (0xB0, was 177) | Ativo |
| 179 | `0x00B3` | `SM_CRAFT_ANIMATION` | [S_COMBINE_OTHER] (0xB3, was 180) | Ativo |
| 180 | `0x00B4` | `SM_CRAFT_UPDATE` | [S_COMBINE] (0xB4, was 181) | Ativo |
| 181 | `0x00B5` | `SM_ASCENSION_MORPH` | [S_PLAY_MODE] (0xB5, was 182) | Mapeado (Não instanciado) |
| 182 | `0x00B6` | `SM_ITEM_USAGE_ANIMATION` | [S_USE_ITEM] (0xB6, was 183) | Ativo |
| 183 | `0x00B7` | `SM_CUSTOM_SETTINGS` | [S_CHANGE_FLAG] (0xB7, was 184) | Ativo |
| 184 | `0x00B8` | `SM_DUEL` | [S_DUEL] (0xB8, was 185) | Ativo |
| 186 | `0x00BA` | `SM_PET_EMOTE` | [S_FUNCTIONAL_PET_MOVE] (0xBA, was 187) | Ativo |
| 188 | `0x00BC` | `SM_DEFAULT_EMOTION_LIST` | [S_DEFAULT_EMOTION_LIST] (0x00BC) | Mapeado (Não instanciado) |
| 190 | `0x00BE` | `SM_QUESTIONNAIRE` | [S_POLL_CONTENTS] (0xBE, was 191) | Ativo |
| 192 | `0x00C0` | `SM_DIE` | [S_RESURRECT_INFO] (0xC0) | Ativo |
| 193 | `0x00C1` | `SM_RESURRECT` | [S_RESURRECT_BY_OTHER] (0xC1) | Ativo |
| 194 | `0x00C2` | `SM_FORCED_MOVE` | [S_MOVEBACK] (0xC2) | Ativo |
| 195 | `0x00C3` | `SM_TELEPORT_MAP` | [S_ROUTEMAP_INFO] (0xC3) | Ativo |
| 196 | `0x00C4` | `SM_USE_OBJECT` | [S_GAUGE] (0xC4): 13 b [D jogador][D objeto][D ms][C 1 início|2 fim] em todas as capturas; 0xC3 é outro pacote, de tamanho variável | Ativo |
| 197 | `0x00C5` | `SM_CREATURE_STATE_UPDATE` | [S_CREATURE_STATE_UPDATE] (0x00C5) | Mapeado (Não instanciado) |
| 198 | `0x00C6` | `SM_L2AUTH_LOGIN_CHECK` | [S_L2AUTH_LOGIN_CHECK] (0xC6, was 199) | Ativo |
| 199 | `0x00C7` | `SM_CHARACTER_LIST` | [S_CHARACTER_LIST] (0xC7, was 200) | Ativo |
| 200 | `0x00C8` | `SM_CREATE_CHARACTER` | [S_CREATE_CHARACTER] (0xC8, was 201) | Ativo |
| 201 | `0x00C9` | `SM_DELETE_CHARACTER` | [S_DELETE_CHARACTER] (0xC9, was 202) | Ativo |
| 202 | `0x00CA` | `SM_RESTORE_CHARACTER` | [S_RESTORE_CHARACTER] (0xCA, was 203) | Ativo |
| 203 | `0x00CB` | `SM_POSITION` | [S_FORCE_BLINK] (0xCB, was 204) | Ativo |
| 204 | `0x00CC` | `SM_LOOT_STATUS` | [S_LOOT] (0xCC, was 205) | Ativo |
| 205 | `0x00CD` | `SM_LOOT_ITEMLIST` | [S_LOOT_ITEMLIST] (0xCD, was 206) | Ativo |
| 206 | `0x00CE` | `SM_RECIPE_LIST` | [S_RECIPE_LIST] (0xCE, was 207) | Ativo |
| 207 | `0x00CF` | `SM_MANTRA_EFFECT` | [S_SKILL_ACTIVATED] (0xCF, was 208) | Ativo |
| 208 | `0x00D0` | `SM_SIEGE_LOCATION_INFO` | [S_ABYSS_INFO] (0xD0, was 209) | Ativo |
| 209 | `0x00D1` | `SM_SIEGE_LOCATION_STATE` | [S_CHANGE_ABYSS_PVP_STATUS] (0xD1, was 210) | Ativo |
| 210 | `0x00D2` | `SM_PLAYER_SEARCH` | [S_SEARCH_USER_RESULT] (0xD2, was 211) | Ativo |
| 212 | `0x00D4` | `SM_LEGION_SEND_EMBLEM` | [S_GUILD_EMBLEM_IMG_BEGIN] (0xD4, was 213) | Ativo |
| 213 | `0x00D5` | `SM_LEGION_SEND_EMBLEM_DATA` | [S_GUILD_EMBLEM_IMG_DATA] (0xD5, was 214) | Ativo |
| 214 | `0x00D6` | `SM_LEGION_UPDATE_EMBLEM` | [S_GUILD_EMBLEM_UPDATED] (0xD6, was 215) | Ativo |
| 215 | `0x00D7` | `SM_PLAYER_ZONES` | [S_SKILL_PENALTY_STATUS] (0xD7) — zone/skill penalty region for self | Mapeado (Não instanciado) |
| 216 | `0x00D8` | `SM_PLAYER_REGION` | [S_SKILL_PENALTY_STATUS_OTHER] (0xD8, was 217) | Mapeado (Não instanciado) |
| 217 | `0x00D9` | `SM_SHIELD_EFFECT` | [S_ABYSS_SHIELD_INFO] (0xD9, was 218) | Ativo |
| 220 | `0x00DC` | `SM_ABYSS_ARTIFACT_INFO3` | [S_ARTIFACT_INFO] (0xDC, was 220) | Ativo |
| 222 | `0x00DE` | `SM_FRIEND_RESPONSE` | [S_BUDDY_RESULT] (0xDE) | Ativo |
| 223 | `0x00DF` | `SM_BLOCK_RESPONSE` | [S_BLOCK_RESULT] (0xDF) | Ativo |
| 224 | `0x00E0` | `SM_BLOCK_LIST` | [S_BLOCK_LIST] (0xE0) | Ativo |
| 225 | `0x00E1` | `SM_FRIEND_NOTIFY` | [S_NOTIFY_BUDDY] (0xE1) | Ativo |
| 226 | `0x00E2` | `SM_TOWNS_LIST` | [S_TOWN_INFO_LIST] (0xE2) | Ativo |
| 227 | `0x00E3` | `SM_FRIEND_STATUS` | [S_CUR_STATUS] (0xE3) | Ativo |
| 229 | `0x00E5` | `SM_CHANNEL_INFO` | [S_CHANGE_CHANNEL] (0xE5) | Ativo |
| 230 | `0x00E6` | `SM_CHAT_INIT` | [S_SIGN_CLIENT] (0xE6) | Ativo |
| 231 | `0x00E7` | `SM_MACRO_LIST` | [S_LOAD_MACRO] (0xE7) | Ativo |
| 232 | `0x00E8` | `SM_MACRO_RESULT` | [S_MACRO_RESULT] (0xE8) | Ativo |
| 233 | `0x00E9` | `SM_NICKNAME_CHECK_RESPONSE` | [S_EXIST_RESULT] (0xE9) | Ativo |
| 235 | `0x00EB` | `SM_BIND_POINT_INFO` | [S_RESURRECT_LOC_INFO] (0xEB) | Ativo |
| 236 | `0x00EC` | `SM_RIFT_ANNOUNCE` | [S_WORLD_INFO] (0xEC) | Ativo |
| 237 | `0x00ED` | `SM_ABYSS_RANK` | [S_ABYSS_POINT] (0xED) | Ativo |
| 238 | `0x00EE` | `SM_ACCOUNT_PROPERTIES` | [S_BUILDER_LEVEL] (0xEE) | Ativo |
| 240 | `0x00F0` | `SM_FRIEND_UPDATE` | [S_BUDDY_DATA] (0xF0) | Ativo |
| 241 | `0x00F1` | `SM_LEARN_RECIPE` | [S_ADD_RECIPE] (0xF1) | Ativo |
| 242 | `0x00F2` | `SM_RECIPE_DELETE` | [S_REMOVE_RECIPE] (0xF2) | Ativo |
| 243 | `0x00F3` | `SM_FORTRESS_INFO` | [S_CHANGE_ABYSS_TELEPORTER_STATUS] (0xF3) | Ativo |
| 244 | `0x00F4` | `SM_FLY_TIME` | [S_FLIGHT_POINT] (0xF4) | Ativo |
| 245 | `0x00F5` | `SM_ALLIANCE_INFO` | [S_ALLIANCE_INFO] (0xF5) | Ativo |
| 246 | `0x00F6` | `SM_ALLIANCE_MEMBER_INFO` | [S_ALLIANCE_MEMBER_INFO] (0xF6) | Ativo |
| 247 | `0x00F7` | `SM_LEAVE_GROUP_MEMBER` | [S_GROUP_INFO] (0xF7) | Ativo |
| 249 | `0x00F9` | `SM_SHOW_BRAND` | [S_TACTICS_SIGN] (0xF9) | Ativo |
| 250 | `0x00FA` | `SM_ALLIANCE_READY_CHECK` | [S_GROUP_READY] (0xFA) | Ativo |
| 252 | `0x00FC` | `SM_PRICES` | [S_TAX_INFO] (0xFC) | Ativo |
| 253 | `0x00FD` | `SM_TRADELIST` | [S_STORE_SALE_INFO] (0xFD) | Ativo |
| 254 | `0x00FE` | `SM_INVINCIBLE_TIME` | [S_INVINCIBLE_TIME] (0xFE) | Ativo |
| 255 | `0x00FF` | `SM_RECONNECT_KEY` | [S_RECONNECT_KEY] (0xFF) | Ativo |
| 256 | `0x0100` | `SM_HOUSE_BIDS` | [S_AUCTION_LIST] (0x100) | Ativo |
| 257 | `0x0101` | `SM_PACKAGE_INFO_NOTIFY` | [S_BM_PACK_LIST] (0x101) | Mapeado (Não instanciado) |
| 258 | `0x0102` | `SM_SECURITY_TOKEN` | [S_REP_WEB_SESSIONKEY] (0x102) | Ativo |
| 259 | `0x0103` | `SM_RECEIVE_BIDS` | [S_AUCTION_BET] (0x103) | Ativo |
| 260 | `0x0104` | `SM_FIRST_SHOW_DECOMPOSABLE` | [S_DISASSEMBLY_ITEMLIST] (0x0104) | Ativo |
| 261 | `0x0105` | `SM_SECONDARY_SHOW_DECOMPOSABLE` | [S_SELECT_DISASSEMBLY_ITEM_RESULT] (0x0105) | Ativo |
| 262 | `0x0106` | `SM_REPLY_NP_LOGIN_GAMESVR` | [S_REPLY_NP_LOGIN_GAMESVR] (0x106) | Ativo |
| 264 | `0x0108` | `SM_REPLY_NP_AUTH_TOKEN` | [S_REPLY_NP_AUTH_TOKEN] (0x108) | Ativo |
| 265 | `0x0109` | `SM_TUTORIAL_GUIDE_STATE` | [S_TUTORIAL_GUIDE_STATE] (0x0109) | Ativo |
| 266 | `0x010A` | `SM_NPSHOP_GOODS_COUNT` | [S_NPSHOP_GOODS_COUNT] (0x10A) | Ativo |
| 268 | `0x010C` | `SM_NPSHOP_GOODS_LIST` | [S_RESPONSE_NPSHOP_GOODS_LIST] (0x10C, captura Black Cloud Mail) | Ativo |
| 269 | `0x010D` | `SM_NPSHOP_GOODS_RECV` | [S_RESPONSE_NPSHOP_GOODS_RECV] (0x10D, captura Black Cloud Mail) | Ativo |
| 270 | `0x010E` | `S_SERVER_ENV` | [S_SERVER_ENV] (0x10E) | Ativo |
| 271 | `0x010F` | `S_PROGRESS_ACHIEVEMENT` | [S_PROGRESS_ACHIEVEMENT] (0x10F) | Ativo |
| 272 | `0x0110` | `SM_ACHIEVEMENT_SEASON_EVENT_INFO` | [S_ACHIEVEMENT_SEASON_EVENT_INFO] (0x0110) | Mapeado (Não instanciado) |
| 274 | `0x0112` | `S_CREATE_ACHIEVEMENT_EVENT` | [S_CREATE_ACHIEVEMENT_EVENT] (0x112, wire 0x102, 68 b) | Ativo |
| 275 | `0x0113` | `SM_SPECIAL_SHOP_ITEM_LIST` | [S_SPECIAL_SHOP_ITEM_LIST] (0x0113) | Mapeado (Não instanciado) |
| 276 | `0x0114` | `S_ACHIEVEMENT_REWARD_NOTI` | [S_ACHIEVEMENT_REWARD_NOTI] (0x114) | Mapeado (Não instanciado) |
| 277 | `0x0115` | `S_CLEAR_ACHIEVEMENT_EVENT` | [S_CLEAR_ACHIEVEMENT_EVENT] (0x115) | Ativo |
| 279 | `0x0117` | `S_BATTLEPASS_LIST` | [S_BATTLEPASS_LIST] (0x117, wire 0x10F, 234 b) | Ativo |
| 280 | `0x0118` | `S_BATTLEPASS_UPDATED` | [S_BATTLEPASS_UPDATED] (0x118, wire 0x108, 232 b) | Ativo |
| 281 | `0x0119` | `S_GAMEPASS_INFO` | [S_GAMEPASS_INFO] (0x119) | Ativo |
| 282 | `0x011A` | `S_GAMEPASS_OTHER_UPDATED` | [S_GAMEPASS_OTHER_UPDATED] (0x11A) | Ativo |
| 283 | `0x011B` | `SM_QUNA` | [SM_QUNA] (0x11B) | Ativo |
| 285 | `0x011D` | `S_READY_ENTER_WORLD` | [S_READY_ENTER_WORLD] (0x11D) | Ativo |
| 288 | `0x0120` | `SM_TUNE_RESULT` | [S_REIDENTIFY_PREVIEW] | Ativo |
| 289 | `0x0121` | `SM_CHAT_ACCUSE` | [S_CHAT_ACCUSE] (0x121) | Ativo |
| 290 | `0x0122` | `SM_USER_CLASSIC_WARDROBE_LOAD` | [S_USER_CLASSIC_WARDROBE_LOAD] (0x122): 58 de 58 logins; 0x123 na lista 2.4 | Ativo |
| 291 | `0x0123` | `SM_USER_CLASSIC_WARDROBE_INFO_UPDATED` | [S_USER_CLASSIC_WARDROBE_INFO_UPDATED] (0x123): sem captura; 0x124 na 2.4 | Ativo |
| 292 | `0x0124` | `SM_USER_CLASSIC_WARDROBE_DATA_UPDATED` | [S_USER_CLASSIC_WARDROBE_DATA_UPDATED] (0x124): 5 de 5; 0x125 na 2.4 | Ativo |
| 293 | `0x0125` | `SM_AFTER_SIEGE_LOCINFO_475` | [S_ABYSS_INFO_GAB1_SPEC] | Mapeado (Não instanciado) |
| 294 | `0x0126` | `SM_SPAM_FILTER_FLAG` | [S_SPAM_FILTER_FLAG] (0x126) | Ativo |
| 295 | `0x0127` | `SM_CUBE_TAB_EXPANSION_INFO` | [S_CUBE_TAB_EXPANSION_INFO] (0x0127) | Mapeado (Não instanciado) |
| 296 | `0x0128` | `SM_BIND_POINT_TELEPORT` | [S_HOTSPOT] | Ativo |
| 297 | `0x0129` | `SM_RECOMMENDED_PLAYERS_LIST` | [S_RECOMMENDED_PLAYERS_LIST] (0x0129) | Mapeado (Não instanciado) |
| 298 | `0x012A` | `SM_UPGRADE_ARCADE` | [S_GOTCHA_NOTIFY] | Ativo |
| 300 | `0x012C` | `SM_CHANNEL_CHATTING_BLACKLIST_SETTING` | [S_CHANNEL_CHATTING_BLACKLIST_SETTING] (0x12C) | Ativo |
| 302 | `0x012E` | `SM_LEGION_DOMINION_RANK` | [S_LEGION_DOMINION_RANKING] | Ativo |
| 303 | `0x012F` | `SM_LOAD_EQUIPMENT_CHANGE` | [S_LOAD_EQUIPMENT_CHANGE] (0x12F) | Ativo |
| 304 | `0x0130` | `SM_RANK_LIST` | [S_RANK_LIST] (0x0130) | Ativo |
| 305 | `0x0131` | `SM_RANK_INFO` | [S_RANK_INFO] (0x0131) | Ativo |
| 307 | `0x0133` | `SM_ENTER_WORLD_CHECK` | [S_ENTER_WORLD_CHECK] (0x133) | Ativo |
| 309 | `0x0135` | `SM_AUTO_GROUP_STATUS` | [S_AUTO_GROUP_STATUS] (0x0135) | Mapeado (Não instanciado) |
| 312 | `0x0138` | `SM_RANKING_BADGE` | [S_RANKING_BADGE] (0x0138) | Ativo |
| 314 | `0x013A` | `SM_LEGION_HOUSING_NOTICE` | [S_LEGION_HOUSING_NOTICE] (0x013A) | Mapeado (Não instanciado) |
| 316 | `0x013C` | `SM_GLOBAL_TRADE_LIST` | [S_GLOBAL_TRADE_LIST] | Ativo |
| 317 | `0x013D` | `SM_GLOBAL_TRADE_MYLIST` | [S_GLOBAL_TRADE_MYLIST] | Ativo |
| 318 | `0x013E` | `SM_GLOBAL_TRADE_BUY` | [S_GLOBAL_TRADE_BUY] | Ativo |
| 319 | `0x013F` | `SM_GLOBAL_TRADE_COMMIT` | [S_GLOBAL_TRADE_COMMIT] | Ativo |
| 320 | `0x0140` | `SM_GLOBAL_TRADE_CANCEL` | [S_GLOBAL_TRADE_CANCEL] | Ativo |
| 321 | `0x0141` | `SM_GLOBAL_TRADE_SALESLOG` | [S_GLOBAL_TRADE_SALESLOG] | Ativo |
| 322 | `0x0142` | `SM_GLOBAL_TRADE_COLLECT` | [S_GLOBAL_TRADE_COLLECT] | Ativo |
| 323 | `0x0143` | `SM_GLOBAL_TRADE_AVG_PRICE` | [S_GLOBAL_TRADE_AVG_PRICE] | Ativo |
| 324 | `0x0144` | `SM_GLOBAL_TRADE_STATE` | [S_GLOBAL_TRADE_STATE] | Ativo |
| 325 | `0x0145` | `SM_GLOBAL_TRADE_HISTORY` | [S_GLOBAL_TRADE_HISTORY] | Ativo |
| 326 | `0x0146` | `SM_PLAYER_OBJECT_ID_ECHO` | [S_PLAYER_OBJECT_ID_ECHO] (0x0146) | Ativo |
| 327 | `0x0147` | `SM_SELL_ITEM` | [S_STORE_PURCHASE_INFO] (0x147) | Ativo |
| 328 | `0x0148` | `SM_COMBAT_TALENT_REWARDS` | [S_COMBAT_POWER_REWARD_INFO] (0x0148) | Ativo |
| 329 | `0x0149` | `SM_COMBAT_TALENT_REWARD_UPDATE` | [S_COMBAT_POWER_REWARD_UPDATE] (0x0149) | Ativo |
| 330 | `0x014A` | `SM_NETWORK_SYNC_ACK` | [S_NETWORK_SYNC_ACK] (0x014A) | Mapeado (Não instanciado) |
| 331 | `0x014B` | `SM_SP_UPDATE` | SP do próprio Revenant (0x014B, 2 b) | Ativo |
| 332 | `0x014C` | `SM_STORYBOOK_FINISHED_LIST` | [S_USER_STORY_BOOK_FINISHED_LIST_LOAD] | Ativo |
| 333 | `0x014D` | `SM_STORYBOOK_REGISTERED_LIST` | [S_USER_STORY_BOOK_REGISTERED_ITEM_LIST_LOAD] | Ativo |
| 334 | `0x014E` | `SM_STORYBOOK_UPDATE` | [S_USER_STORY_BOOK_UPDATE_RESULT], resposta ao C 0xE4 | Ativo |
| 336 | `0x0150` | `SM_LEGION_SEARCH_LIST` | resultado da busca de Legion (0x0150) | Ativo |
| 337 | `0x0151` | `SM_LEGION_APPLICATION` | candidatura do personagem (0x0151) | Ativo |
| 338 | `0x0152` | `SM_LEGION_APPLICANT_LIST` | candidatos da Legion (0x0152) | Ativo |
| 339 | `0x0153` | `SM_LEGION_APPLICANT_ADD` | candidato novo para o membro online (0x0153) | Ativo |
| 340 | `0x0154` | `SM_LEGION_APPLICANT_RESULT` | aceite ou recusa de candidato (0x0154) | Ativo |
| 342 | `0x0156` | `SM_LEGION_DONATION_MEMBERS` | pontos de produção por membro (0x0156) | Ativo |
| 343 | `0x0157` | `SM_LEGION_DONATION_POINTS` | pontos de produção da Legion no dia (0x0157) | Ativo |
| 344 | `0x0158` | `SM_LEGION_DONATION_STATUS` | produções hoje e dias seguidos (0x0158) | Ativo |
| 345 | `0x0159` | `SM_LEGION_DONATION_LIST` | lista de produção do dia (0x0159) | Ativo |
| 346 | `0x015A` | `SM_LEGION_CRAFT_LIST` | receitas de produção da Legion (0x015A) | Ativo |
| 348 | `0x015C` | `SM_LEGION_MISSION_LIST` | missões da Legion (0x015C) | Ativo |
| 349 | `0x015D` | `SM_LEGION_MISSION_UPDATE` | progresso de missão da Legion (0x015D) | Ativo |
| 350 | `0x015E` | `SM_LEGION_TERRITORY_INFO` | [S_LEGION_TERRITORY_INFO] (0x015E) | Mapeado (Não instanciado) |
| 355 | `0x0163` | `SM_LEGION_ESSENCE` | essência e fragmentos da Legion (0x0163) | Ativo |
| 356 | `0x0164` | `SM_LEGION_GROWTH` | nível e exp de crescimento da Legion (0x0164) | Ativo |
| 357 | `0x0165` | `SM_LEGION_COIN` | moedas pessoais da Legion (0x0165) | Ativo |
| 358 | `0x0166` | `SM_SP_UPDATE_OTHER` | SP de um jogador para quem o vê (0x0166, 6 b) | Ativo |
| 359 | `0x0167` | `SM_LEGION_CRAFT_BOOKMARK` | favorito de produção da Legion (0x0167) | Ativo |
| 361 | `0x0169` | `SM_MOROS_INFO` | Moreth, Chronicle of Time: [H nível][D pontos][D 0][H registros] (40 de 40 capturas) | Ativo |
| 363 | `0x016B` | `SM_ALTER_INFO` | [S_ALTER_INFO] (0x016B) | Ativo |
| 368 | `0x0170` | `SM_ZONE_HAZARD_LIST` | [S_ZONE_HAZARD_LIST] (0x0170) | Mapeado (Não instanciado) |
| 369 | `0x0171` | `SM_STORYBOOK_APPRAISE_RESULT` | identificação de fragmentos, resposta ao C 0xDC | Ativo |
| 370 | `0x0172` | `SM_STORYBOOK_DISASSEMBLE_RESULT` | desmontagem de fragmentos, resposta ao C 0xDD | Ativo |
| 371 | `0x0173` | `SM_EQUIP_SLOT_UPDATE` | [S_EQUIP_SLOT_UPDATE] (0x0173) | Mapeado (Não instanciado) |
| 373 | `0x0175` | `SM_EP_UPDATE` | EP (Ki) do próprio Brawler (0x0175, 2 b) | Ativo |
| 374 | `0x0176` | `SM_EP_UPDATE_OTHER` | EP de um jogador para quem o vê (0x0176, 6 b) | Ativo |
| 375 | `0x0177` | `SM_EQUIPMENT_VIEW_STATE` | [S_EQUIPMENT_VIEW_STATE] (0x0177) | Ativo |
| 383 | `0x017F` | `SM_PROTOCOL_VERSION` | [S_PROTOCOL_VERSION] (0x017F) | Mapeado (Não instanciado) |
| 384 | `0x0180` | `SM_WORLD_VARIABLE` | [S_WORLD_VARIABLE] (0x0180) — variaveis de mundo do mapa | Ativo |
| 385 | `0x0181` | `SM_COMBAT_BURST_EFFECT` | [S_COMBAT_BURST_EFFECT] (0x0181) | Mapeado (Não instanciado) |
| 386 | `0x0182` | `SM_COMBAT_BURST_REMOVE` | [S_COMBAT_BURST_REMOVE] (0x0182) | Mapeado (Não instanciado) |
| 387 | `0x0183` | `SM_CAMERA_VIEW_MODE` | [S_CAMERA_VIEW_MODE] (0x0183) | Mapeado (Não instanciado) |
| 391 | `0x0187` | `SM_CAMP_PVP_ZONE` | [S_ZONE_PVP] (0x0187) — zona PvP das torres de Tiamaranta | Ativo |
| 396 | `0x018C` | `SM_TERRAIN_SECTOR_INFO` | [S_TERRAIN_SECTOR_INFO] (0x018C) | Mapeado (Não instanciado) |
| 401 | `0x0191` | `SM_RENDER_GRAPHIC_INIT` | [S_RENDER_GRAPHIC_INIT] (0x0191) | Ativo |
| 407 | `0x0197` | `SM_AVATAR_PRESENCE_INIT` | [S_AVATAR_PRESENCE_INIT] (0x0197) | Ativo |
| 413 | `0x019D` | `SM_ZONE_STATE_LIST` | [S_ZONE_STATE_LIST] (0x019D) — lista de zonas do mapa na entrada | Ativo |
| 415 | `0x019F` | `S_DAEVA_PASS_DATA` | [S_DAEVA_PASS_DATA] (0x19F) | Mapeado (Não instanciado) |
| 418 | `0x01A2` | `SM_SIEL_HAMMER_RESULT` |  | Ativo |
| 419 | `0x01A3` | `SM_SIEL_ANVIL_START` |  | Ativo |
| 420 | `0x01A4` | `SM_SIEL_ANVIL_RESULT` |  | Ativo |
| 422 | `0x01A6` | `SM_ITEM_COMPOSE_EVENT` |  | Ativo |
| 423 | `0x01A7` | `SM_ITEM_COMPOSE_RESULT` |  | Ativo |
| 424 | `0x01A8` | `SM_AVATAR_PRESENCE_SYNC` | [S_AVATAR_PRESENCE_SYNC] (0x01A8) | Ativo |
| 426 | `0x01AA` | `SM_COSMETIC_TITLE_INIT` | [S_COSMETIC_TITLE_INIT] (0x01AA) | Mapeado (Não instanciado) |
| 427 | `0x01AB` | `SM_SIEL_ANVIL_POINTS_INFO` | [S_SIEL_ANVIL_POINTS_INFO] (0x01AB) | Ativo |
| 428 | `0x01AC` | `SM_MAP_ZONE_BOUNDS` | [S_MAP_ZONE_BOUNDS] (0x01AC) | Mapeado (Não instanciado) |
| 429 | `0x01AD` | `SM_ITEM_UPGRADE_EVENT` | [S_ITEM_UPGRADE_EVENT] | Ativo |
| 430 | `0x01AE` | `SM_ITEM_UPGRADE_RESULT` | [S_ITEM_UPGRADE_RESULT] | Ativo |
| 431 | `0x01AF` | `SM_RADAR_INITIAL_STATE` | [S_RADAR_INITIAL_STATE] (0x01AF) | Mapeado (Não instanciado) |
| 435 | `0x01B3` | `SM_MAILBOX_INITIAL_STATUS` | [S_MAILBOX_INITIAL_STATUS] (0x01B3) | Mapeado (Não instanciado) |
| 437 | `0x01B5` | `SM_RANKING_READY` | [S_UNK_01B5] (0x1B5) | Ativo |
| 442 | `0x01BA` | `SM_REGION_CHAT_CHANNEL_INFO` | [S_REGION_CHAT_CHANNEL_INFO] (0x01BA) | Ativo |
| 445 | `0x01BD` | `SM_HUNT_OBJECTIVE_PROGRESS` | [S_HUNT_OBJECTIVE_PROGRESS] (0x01BD) | Mapeado (Não instanciado) |
| 448 | `0x01C0` | `SM_TUTORIAL_LOAD_COMPLETED` | [S_TUTORIAL_LOAD_COMPLETED] (0x01C0) | Ativo |
| 450 | `0x01C2` | `SM_CHALLENGE_GUIDE_TABS` | [S_CHALLENGE_GUIDE_TABS] (0x01C2) | Ativo |
| 451 | `0x01C3` | `SM_CLASSIC_ENCHANT_ANIMATION` |  | Ativo |
| 452 | `0x01C4` | `SM_SIEL_HAMMER_EVENT` |  | Ativo |
| 453 | `0x01C5` | `SM_ENTER_WORLD_HANDSHAKE_ACK` | [S_ENTER_WORLD_HANDSHAKE_ACK] (0x01C5) | Mapeado (Não instanciado) |
