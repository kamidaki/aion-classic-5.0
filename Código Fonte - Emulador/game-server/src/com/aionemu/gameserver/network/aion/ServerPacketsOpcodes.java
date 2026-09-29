package com.aionemu.gameserver.network.aion;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import com.aionemu.gameserver.network.aion.serverpackets.*;

/**
 * @author Lost Academy Team & Durak
 */
public class ServerPacketsOpcodes {

	private static final Map<Class<? extends AionServerPacket>, Integer> opcodes = new ConcurrentHashMap<>();

	static {
		addPacketOpcode(0, SM_VERSION_CHECK.class); // [S_VERSION_CHECK]
		addPacketOpcode(1, SM_STATS_INFO.class); // [S_STATUS]
		addPacketOpcode(2, SM_GM_SHOW_PLAYER_STATUS.class); // [S_STATUS_OTHER]
		addPacketOpcode(3, SM_STATUPDATE_HP.class); // [S_HIT_POINT]
		addPacketOpcode(4, SM_STATUPDATE_MP.class); // [S_MANA_POINT]
		addPacketOpcode(5, SM_ATTACK_STATUS.class); // [S_HIT_POINT_OTHER]
		addPacketOpcode(6, SM_STATUPDATE_DP.class); // [S_DP]
		addPacketOpcode(7, SM_DP_INFO.class); // [S_DP_USER]
		addPacketOpcode(8, SM_STATUPDATE_EXP.class); // [S_EXP]
		// addPacketOpcode(9, ); // [S_LOGIN_CHECK]
		addPacketOpcode(10, SM_NPC_ASSEMBLER.class); // [S_CUTSCENE_NPC_INFO]
		addPacketOpcode(11, SM_LEGION_UPDATE_NICKNAME.class); // [S_CHANGE_GUILD_MEMBER_NICKNAME]
		addPacketOpcode(12, SM_LEGION_HISTORY.class); // [S_GUILD_HISTORY]
		addPacketOpcode(13, SM_TUTORIAL_HINT.class); // [S_TUTORIAL_HINT] 5.0 Classic
		addPacketOpcode(14, SM_NPC_INFO.class); // [S_PUT_NPC]
		addPacketOpcode(15, SM_PLAYER_SPAWN.class); // [S_WORLD]
		// addPacketOpcode(16, ); // [S_DUMMY_PACKET]
		addPacketOpcode(17, SM_GATHERABLE_INFO.class); // [S_PUT_OBJECT]
		// addPacketOpcode(18, ); // [S_PUT_VEHICLE]
		addPacketOpcode(19, SM_GM_SEARCH.class); // [S_BUILDER_RESULT]
		addPacketOpcode(20, SM_TELEPORT_LOC.class); // [S_REQUEST_TELEPORT]
		addPacketOpcode(21, SM_POSITION_SELF.class); // [S_BLINK]
		addPacketOpcode(22, SM_DELETE.class); // [S_REMOVE_OBJECT]
		addPacketOpcode(23, SM_LOGIN_QUEUE.class); // [S_WAIT_LIST]
		addPacketOpcode(24, SM_MESSAGE.class); // [S_MESSAGE]
		addPacketOpcode(25, SM_SYSTEM_MESSAGE.class); // [S_MESSAGE_CODE]
		addPacketOpcode(26, SM_INVENTORY_INFO.class); // [S_LOAD_INVENTORY]
		addPacketOpcode(27, SM_INVENTORY_ADD_ITEM.class); // [S_ADD_INVENTORY]
		addPacketOpcode(28, SM_DELETE_ITEM.class); // [S_REMOVE_INVENTORY]
		addPacketOpcode(29, SM_INVENTORY_UPDATE_ITEM.class); // [S_CHANGE_ITEM_DESC]
		addPacketOpcode(30, SM_UI_SETTINGS.class); // [S_LOAD_CLIENT_SETTINGS]
		addPacketOpcode(31, SM_PLAYER_STANCE.class); // [S_CHANGE_STANCE]
		addPacketOpcode(32, SM_PLAYER_INFO.class); // [S_PUT_USER]
		addPacketOpcode(33, SM_CASTSPELL.class); // [S_USE_SKILL]
		addPacketOpcode(34, SM_GATHER_ANIMATION.class); // [S_GATHER_OTHER]
		addPacketOpcode(35, SM_GATHER_UPDATE.class); // [S_GATHER]
		addPacketOpcode(36, SM_UPDATE_PLAYER_APPEARANCE.class); // [S_WIELD]
		addPacketOpcode(37, SM_EMOTION.class); // [S_ACTION]
		addPacketOpcode(38, SM_GAME_TIME.class); // [S_TIME]
		addPacketOpcode(39, SM_TIME_CHECK.class); // [S_SYNC_TIME]
		addPacketOpcode(40, SM_LOOKATOBJECT.class); // [S_NPC_CHANGED_TARGET]
		addPacketOpcode(41, SM_TARGET_SELECTED.class); // [S_TARGET_INFO]
		addPacketOpcode(42, SM_SKILL_CANCEL.class); // [S_SKILL_CANCELED]
		addPacketOpcode(43, SM_CASTSPELL_RESULT.class); // [S_SKILL_SUCCEDED]
		addPacketOpcode(44, SM_SKILL_LIST.class); // [S_ADD_SKILL]
		addPacketOpcode(45, SM_SKILL_REMOVE.class); // [S_DELETE_SKILL]
		addPacketOpcode(46, SM_SKILL_ACTIVATION.class); // [S_TOGGLE_SKILL_ON_OFF]
		// addPacketOpcode(47, ); // [S_ADD_MAINTAIN_SKILL]
		// addPacketOpcode(48, ); // [S_DELETE_MAINTAIN_SKILL]
		addPacketOpcode(49, SM_ABNORMAL_STATE.class); // [S_ABNORMAL_STATUS]
		addPacketOpcode(50, SM_ABNORMAL_EFFECT.class); // [S_ABNORMAL_STATUS_OTHER]
		addPacketOpcode(51, SM_SKILL_COOLDOWN.class); // [S_LOAD_SKILL_COOLTIME]
		addPacketOpcode(52, SM_QUESTION_WINDOW.class); // [S_ASK]
		addPacketOpcode(53, SM_CLOSE_QUESTION_WINDOW.class); // [S_CANCEL_ASK]
		addPacketOpcode(54, SM_ATTACK.class); // [S_ATTACK]
		addPacketOpcode(55, SM_MOVE.class); // [S_MOVE_NEW]
		// addPacketOpcode(56, ); // [S_MOVE_OBJECT]
		addPacketOpcode(57, SM_HEADING_UPDATE.class); // [S_CHANGE_DIRECTION]
		addPacketOpcode(58, SM_TRANSFORM.class); // [S_POLYMORPH]
		addPacketOpcode(59, SM_GM_SHOW_PLAYER_SKILLS.class); // [S_SKILL_OTHER]
		addPacketOpcode(60, SM_DIALOG_WINDOW.class); // [S_NPC_HTML_MESSAGE]
		// -1 Opcode Shift for Classic 5.0 (housing packets removed)
		addPacketOpcode(64, SM_VIEW_PLAYER_DETAILS.class); // [S_ITEM_LIST] (0x40, was 65)
		addPacketOpcode(66, SM_WEATHER.class); // [S_WEATHER] (0x42, was 67)
		addPacketOpcode(67, SM_PLAYER_STATE.class); // [S_INVISIBLE_LEVEL] (0x43, was 68)
		// addPacketOpcode(68, SM_RECALLED_BY_OTHER.class); // [S_RECALLED_BY_OTHER] (0x44, was 69)
		addPacketOpcode(69, SM_ACTION_ANIMATION.class); // [S_EFFECT] (0x45, was 70)
		addPacketOpcode(70, SM_QUEST_LIST.class); // [S_LOAD_WORKINGQUEST] (0x46, was 71)
		addPacketOpcode(71, SM_KEY.class); // [S_KEY] (0x47, was 72)
		addPacketOpcode(72, SM_SUMMON_PANEL_REMOVE.class); // [S_RESET_SKILL_COOLING_TIME] (0x48, was 73)
		addPacketOpcode(73, SM_EXCHANGE_REQUEST.class); // [S_XCHG_START] (0x49, was 74)
		addPacketOpcode(74, SM_EXCHANGE_ADD_ITEM.class); // [S_ADD_XCHG] (0x4A, was 75)
		// addPacketOpcode(75, ); // [S_REMOVE_XCHG] (0x4B)
		addPacketOpcode(76, SM_EXCHANGE_ADD_KINAH.class); // [S_XCHG_GOLD] (0x4C, was 77)
		addPacketOpcode(77, SM_EXCHANGE_CONFIRMATION.class); // [S_XCHG_RESULT] (0x4D, was 78)
		addPacketOpcode(78, SM_EMOTION_LIST.class); // [S_ADDREMOVE_SOCIAL] (0x4E, was 79)
		// addPacketOpcode(79, ); // [S_CHECK_MESSAGE] (0x4F)
		addPacketOpcode(80, SM_TARGET_UPDATE.class); // [S_USER_CHANGED_TARGET] (0x50, was 81)
		// 82 was SM_HOUSE_EDIT (removed)
		addPacketOpcode(82, SM_PLASTIC_SURGERY.class); // [S_EDIT_CHARACTER] (0x52, was 83)
		// addPacketOpcode(83, SM_CONQUEROR_PROTECTOR.class); // [S_SERIAL_KILLER_LIST] (0x53, was 84)
		addPacketOpcode(84, SM_INFLUENCE_RATIO.class); // [S_ABYSS_NEXT_PVP_CHANGE_TIME] (0x54, was 85)
		addPacketOpcode(85, SM_FORTRESS_STATUS.class); // [S_ABYSS_CHANGE_NEXT_PVP_STATUS] (0x55, was 86)
		addPacketOpcode(86, SM_CAPTCHA.class); // [S_CAPTCHA] (0x56, was 87)
		addPacketOpcode(87, SM_RENAME.class); // [S_ADDED_SERVICE_CHANGE] (0x57, was 88)
		addPacketOpcode(88, SM_SHOW_NPC_ON_MAP.class); // [S_FIND_NPC_POS_RESULT] (0x58, was 89)
		addPacketOpcode(89, SM_GROUP_INFO.class); // [S_PARTY_INFO] (0x59, was 90)
		addPacketOpcode(90, SM_GROUP_MEMBER_INFO.class); // [S_PARTY_MEMBER_INFO] (0x5A, was 91)
		addPacketOpcode(97, SM_QUIT_RESPONSE.class); // [S_ASK_QUIT_RESULT] (0x61, was 98)
		addPacketOpcode(98, SM_CHAT_WINDOW.class); // [S_ASK_INFO_RESULT] (0x62, was 99)
		addPacketOpcode(100, SM_PET.class); // [S_FUNCTIONAL_PET] (0x64, was 101)
		addPacketOpcode(102, SM_ITEM_COOLDOWN.class); // [S_LOAD_ITEM_COOLTIME] (0x66, was 103)
		addPacketOpcode(103, SM_UPDATE_NOTE.class); // [S_TODAY_WORDS] (0x67, was 104)
		addPacketOpcode(104, SM_PLAY_MOVIE.class); // [S_PLAY_CUTSCENE] (0x68, was 105)
		addPacketOpcode(109, SM_LEGION_INFO.class); // [S_GUILD_INFO] (0x6D, was 110)
		addPacketOpcode(110, SM_LEGION_ADD_MEMBER.class); // [S_ADD_GUILD_MEMBER] (0x6E, was 111)
		addPacketOpcode(111, SM_LEGION_LEAVE_MEMBER.class); // [S_DELETE_GUILD_MEMBER] (0x6F, was 112)
		addPacketOpcode(112, SM_LEGION_UPDATE_MEMBER.class); // [S_CHANGE_GUILD_MEMBER_INFO] (0x70, was 113)
		addPacketOpcode(113, SM_LEGION_UPDATE_TITLE.class); // [S_CHANGE_GUILD_OTHER] (0x71, was 114)
		addPacketOpcode(114, SM_ATTACK_RESPONSE.class); // [S_ATTACK_RESULT] (0x72, was 115)
		// 116 was SM_HOUSE_REGISTRY (removed)
		addPacketOpcode(118, SM_LEGION_UPDATE_SELF_INTRO.class); // [S_CHANGE_GUILD_MEMBER_INTRO] (0x76, was 119)
		addPacketOpcode(120, SM_INSTANCE_SCORE.class); // [S_INSTANT_DUNGEON_INFO] (0x78, was 121)
		addPacketOpcode(121, SM_AUTO_GROUP.class); // [S_MATCHMAKER_INFO] (0x79, was 122)
		addPacketOpcode(122, SM_QUEST_COMPLETED_LIST.class); // [S_LOAD_FINISHEDQUEST] (0x7A, was 123)
		addPacketOpcode(123, SM_QUEST_ACTION.class); // [S_QUEST] (0x7B, was 124)
		addPacketOpcode(126, SM_NEARBY_QUESTS.class); // [S_UPDATE_ZONE_QUEST] (0x7E, was 127)
		addPacketOpcode(127, SM_PING_RESPONSE.class); // [S_PING] (0x7F, was 128)
		addPacketOpcode(129, SM_CUBE_UPDATE.class); // [S_EVENT] (0x81, was 130)
		// 131 was SM_HOUSE_SCRIPTS (removed)
		addPacketOpcode(131, SM_FRIEND_LIST.class); // [S_BUDDY_LIST] (0x83, was 132)
		addPacketOpcode(133, SM_PRIVATE_STORE.class); // [S_SHOP_SELL_LIST] (0x85, was 134)
		addPacketOpcode(134, SM_GROUP_LOOT.class); // [S_GROUP_ITEM_DIST] (0x86, was 135)
		addPacketOpcode(135, SM_ABYSS_RANK_UPDATE.class); // [S_ETC_STATUS] (0x87, was 136)
		addPacketOpcode(136, SM_MAY_LOGIN_INTO_GAME.class); // [S_SA_ACCOUNT_ITEM_NOTI] (0x88, was 137)
		addPacketOpcode(137, SM_ABYSS_RANKING_PLAYERS.class); // [S_ABYSS_RANKER_INFOS] (0x89, was 138)
		addPacketOpcode(138, SM_ABYSS_RANKING_LEGIONS.class); // [S_ABYSS_GUILD_INFOS] (0x8A, was 139)
		addPacketOpcode(139, SM_WORLD_SCENE_STATUS.class); // [S_WORLD_SCENE_STATUS] (0x8B)
		addPacketOpcode(140, SM_INSTANCE_INFO.class); // [S_INSTANCE_DUNGEON_COOLTIMES] (0x8C, was 141)
		addPacketOpcode(141, SM_PONG.class); // [S_ALIVE] (0x8D, was 142)
		addPacketOpcode(143, SM_KISK_UPDATE.class); // [S_PLACEABLE_BINDSTONE_INFO] (0x8F, was 144)
		addPacketOpcode(144, SM_PRIVATE_STORE_NAME.class); // [S_PERSONAL_SHOP] (0x90, was 145)
		addPacketOpcode(145, SM_BROKER_SERVICE.class); // [S_VENDOR] (0x91, was 146)
		addPacketOpcode(147, SM_MOTION.class); // [S_CUSTOM_ANIM] (0x93, was 148)
		addPacketOpcode(150, SM_TRADE_IN_LIST.class); // [S_TRADE_IN] (0x96)
		addPacketOpcode(152, SM_SUMMON_PANEL.class); // [S_ADD_PET] (0x98)
		addPacketOpcode(153, SM_SUMMON_OWNER_REMOVE.class); // [S_REMOVE_PET] (0x99)
		addPacketOpcode(154, SM_SUMMON_UPDATE.class); // [S_CHANGE_PET_STATUS] (0x9A)
		addPacketOpcode(155, SM_TRANSFORM_IN_SUMMON.class); // [S_CHANGE_MASTER] (0x9B)
		addPacketOpcode(156, SM_LEGION_MEMBERLIST.class); // [S_GUILD_MEMBER_INFO] (0x9C)
		addPacketOpcode(157, SM_LEGION_EDIT.class); // [S_CHANGE_GUILD_INFO] (0x9D)
		addPacketOpcode(160, SM_MAIL_SERVICE.class); // [S_MAIL] (0xA0, was 161)
		addPacketOpcode(161, SM_SUMMON_USESKILL.class); // [S_ALLOW_PET_USE_SKILL] (0xA1, was 162)
		addPacketOpcode(162, SM_WINDSTREAM.class); // [S_WIND_PATH_RESULT] (0xA2, was 163)
		addPacketOpcode(163, SM_WINDSTREAM_ANNOUNCE.class); // [S_WIND_STATE_INFO] (0xA3, was 164)
		addPacketOpcode(164, SM_RECIPE_COOLDOWN.class); // [S_LOAD_GATHERCOMBINE_COOLTIME] (0xA4, was 165)
		addPacketOpcode(165, SM_FIND_GROUP.class); // [S_PARTY_MATCH] (0xA5, was 166)
		addPacketOpcode(166, SM_REPURCHASE.class); // [S_USER_SELL_HISTORY_LIST] (0xA6, was 167)
		addPacketOpcode(167, SM_WAREHOUSE_INFO.class); // [S_LOAD_WAREHOUSE] (0xA7, was 168)
		addPacketOpcode(168, SM_WAREHOUSE_ADD_ITEM.class); // [S_ADD_WAREHOUSE] (0xA8, was 169)
		addPacketOpcode(169, SM_DELETE_WAREHOUSE_ITEM.class); // [S_REMOVE_WAREHOUSE] (0xA9, was 170)
		addPacketOpcode(170, SM_WAREHOUSE_UPDATE_ITEM.class); // [S_CHANGE_WAREHOUSE_ITEM_DESC] (0xAA, was 171)
		addPacketOpcode(175, SM_TITLE_INFO.class); // [S_TITLE] (0xAF, was 176)
		addPacketOpcode(176, SM_CHARACTER_SELECT.class); // [S_2ND_PASSWORD] (0xB0, was 177)
		addPacketOpcode(179, SM_CRAFT_ANIMATION.class); // [S_COMBINE_OTHER] (0xB3, was 180)
		addPacketOpcode(180, SM_CRAFT_UPDATE.class); // [S_COMBINE] (0xB4, was 181)
		addPacketOpcode(181, SM_ASCENSION_MORPH.class); // [S_PLAY_MODE] (0xB5, was 182)
		addPacketOpcode(182, SM_ITEM_USAGE_ANIMATION.class); // [S_USE_ITEM] (0xB6, was 183)
		addPacketOpcode(183, SM_CUSTOM_SETTINGS.class); // [S_CHANGE_FLAG] (0xB7, was 184)
		addPacketOpcode(184, SM_DUEL.class); // [S_DUEL] (0xB8, was 185)
		addPacketOpcode(186, SM_PET_EMOTE.class); // [S_FUNCTIONAL_PET_MOVE] (0xBA, was 187)
		addPacketOpcode(190, SM_QUESTIONNAIRE.class); // [S_POLL_CONTENTS] (0xBE, was 191)
		addPacketOpcode(192, SM_DIE.class); // [S_RESURRECT_INFO] (0xC0)
		addPacketOpcode(193, SM_RESURRECT.class); // [S_RESURRECT_BY_OTHER] (0xC1)
		addPacketOpcode(194, SM_FORCED_MOVE.class); // [S_MOVEBACK] (0xC2)
		addPacketOpcode(195, SM_TELEPORT_MAP.class); // [S_ROUTEMAP_INFO] (0xC3)
		addPacketOpcode(196, SM_USE_OBJECT.class); // [S_GAUGE] (0xC4): 13 b [D jogador][D objeto][D ms][C 1 início|2 fim] em todas as capturas; 0xC3 é outro pacote, de tamanho variável
		addPacketOpcode(198, SM_L2AUTH_LOGIN_CHECK.class); // [S_L2AUTH_LOGIN_CHECK] (0xC6, was 199)
		addPacketOpcode(199, SM_CHARACTER_LIST.class); // [S_CHARACTER_LIST] (0xC7, was 200)
		addPacketOpcode(200, SM_CREATE_CHARACTER.class); // [S_CREATE_CHARACTER] (0xC8, was 201)
		addPacketOpcode(201, SM_DELETE_CHARACTER.class); // [S_DELETE_CHARACTER] (0xC9, was 202)
		addPacketOpcode(202, SM_RESTORE_CHARACTER.class); // [S_RESTORE_CHARACTER] (0xCA, was 203)
		addPacketOpcode(203, SM_POSITION.class); // [S_FORCE_BLINK] (0xCB, was 204)
		addPacketOpcode(204, SM_LOOT_STATUS.class); // [S_LOOT] (0xCC, was 205)
		addPacketOpcode(205, SM_LOOT_ITEMLIST.class); // [S_LOOT_ITEMLIST] (0xCD, was 206)
		addPacketOpcode(206, SM_RECIPE_LIST.class); // [S_RECIPE_LIST] (0xCE, was 207)
		addPacketOpcode(207, SM_MANTRA_EFFECT.class); // [S_SKILL_ACTIVATED] (0xCF, was 208)
		addPacketOpcode(208, SM_SIEGE_LOCATION_INFO.class); // [S_ABYSS_INFO] (0xD0, was 209)
		addPacketOpcode(209, SM_SIEGE_LOCATION_STATE.class); // [S_CHANGE_ABYSS_PVP_STATUS] (0xD1, was 210)
		addPacketOpcode(210, SM_PLAYER_SEARCH.class); // [S_SEARCH_USER_RESULT] (0xD2, was 211)
		addPacketOpcode(212, SM_LEGION_SEND_EMBLEM.class); // [S_GUILD_EMBLEM_IMG_BEGIN] (0xD4, was 213)
		addPacketOpcode(213, SM_LEGION_SEND_EMBLEM_DATA.class); // [S_GUILD_EMBLEM_IMG_DATA] (0xD5, was 214)
		addPacketOpcode(214, SM_LEGION_UPDATE_EMBLEM.class); // [S_GUILD_EMBLEM_UPDATED] (0xD6, was 215)
		addPacketOpcode(215, SM_PLAYER_ZONES.class); // [S_SKILL_PENALTY_STATUS] (0xD7) — zone/skill penalty region for self
		addPacketOpcode(216, SM_PLAYER_REGION.class); // [S_SKILL_PENALTY_STATUS_OTHER] (0xD8, was 217)
		addPacketOpcode(217, SM_SHIELD_EFFECT.class); // [S_ABYSS_SHIELD_INFO] (0xD9, was 218)
		addPacketOpcode(220, SM_ABYSS_ARTIFACT_INFO3.class); // [S_ARTIFACT_INFO] (0xDC, was 220)
		// Stop -1 shift
		// 221 was SM_HOUSE_TELEPORT (removed)
		addPacketOpcode(222, SM_FRIEND_RESPONSE.class); // [S_BUDDY_RESULT] (0xDE)
		addPacketOpcode(223, SM_BLOCK_RESPONSE.class); // [S_BLOCK_RESULT] (0xDF)
		addPacketOpcode(224, SM_BLOCK_LIST.class); // [S_BLOCK_LIST] (0xE0)
		addPacketOpcode(225, SM_FRIEND_NOTIFY.class); // [S_NOTIFY_BUDDY] (0xE1)
		addPacketOpcode(226, SM_TOWNS_LIST.class); // [S_TOWN_INFO_LIST] (0xE2)
		addPacketOpcode(227, SM_FRIEND_STATUS.class); // [S_CUR_STATUS] (0xE3)
		addPacketOpcode(229, SM_CHANNEL_INFO.class); // [S_CHANGE_CHANNEL] (0xE5)
		addPacketOpcode(230, SM_CHAT_INIT.class); // [S_SIGN_CLIENT] (0xE6)
		addPacketOpcode(231, SM_MACRO_LIST.class); // [S_LOAD_MACRO] (0xE7)
		addPacketOpcode(232, SM_MACRO_RESULT.class); // [S_MACRO_RESULT] (0xE8)
		addPacketOpcode(233, SM_NICKNAME_CHECK_RESPONSE.class); // [S_EXIST_RESULT] (0xE9)
		addPacketOpcode(235, SM_BIND_POINT_INFO.class); // [S_RESURRECT_LOC_INFO] (0xEB)
		addPacketOpcode(236, SM_RIFT_ANNOUNCE.class); // [S_WORLD_INFO] (0xEC)
		addPacketOpcode(237, SM_ABYSS_RANK.class); // [S_ABYSS_POINT] (0xED)
		addPacketOpcode(238, SM_ACCOUNT_PROPERTIES.class); // [S_BUILDER_LEVEL] (0xEE)
		addPacketOpcode(240, SM_FRIEND_UPDATE.class); // [S_BUDDY_DATA] (0xF0)
		addPacketOpcode(241, SM_LEARN_RECIPE.class); // [S_ADD_RECIPE] (0xF1)
		addPacketOpcode(242, SM_RECIPE_DELETE.class); // [S_REMOVE_RECIPE] (0xF2)
		addPacketOpcode(243, SM_FORTRESS_INFO.class); // [S_CHANGE_ABYSS_TELEPORTER_STATUS] (0xF3)
		addPacketOpcode(244, SM_FLY_TIME.class); // [S_FLIGHT_POINT] (0xF4)
		addPacketOpcode(245, SM_ALLIANCE_INFO.class); // [S_ALLIANCE_INFO] (0xF5)
		addPacketOpcode(246, SM_ALLIANCE_MEMBER_INFO.class); // [S_ALLIANCE_MEMBER_INFO] (0xF6)
		addPacketOpcode(247, SM_LEAVE_GROUP_MEMBER.class); // [S_GROUP_INFO] (0xF7)
		addPacketOpcode(249, SM_SHOW_BRAND.class); // [S_TACTICS_SIGN] (0xF9)
		addPacketOpcode(250, SM_ALLIANCE_READY_CHECK.class); // [S_GROUP_READY] (0xFA)
		addPacketOpcode(252, SM_PRICES.class); // [S_TAX_INFO] (0xFC)
		addPacketOpcode(253, SM_TRADELIST.class); // [S_STORE_SALE_INFO] (0xFD)
		addPacketOpcode(254, SM_INVINCIBLE_TIME.class); // [S_INVINCIBLE_TIME] (0xFE)
		addPacketOpcode(255, SM_RECONNECT_KEY.class); // [S_RECONNECT_KEY] (0xFF)
		addPacketOpcode(256, SM_HOUSE_BIDS.class); // [S_AUCTION_LIST] (0x100)
		addPacketOpcode(257, SM_PACKAGE_INFO_NOTIFY.class); // [S_BM_PACK_LIST] (0x101)
		addPacketOpcode(258, SM_SECURITY_TOKEN.class); // [S_REP_WEB_SESSIONKEY] (0x102)
		addPacketOpcode(259, SM_RECEIVE_BIDS.class); // [S_AUCTION_BET] (0x103)
		addPacketOpcode(262, SM_REPLY_NP_LOGIN_GAMESVR.class); // [S_REPLY_NP_LOGIN_GAMESVR] (0x106)
		addPacketOpcode(264, SM_REPLY_NP_AUTH_TOKEN.class); // [S_REPLY_NP_AUTH_TOKEN] (0x108)
		addPacketOpcode(266, SM_NPSHOP_GOODS_COUNT.class); // [S_NPSHOP_GOODS_COUNT] (0x10A)
		addPacketOpcode(268, SM_NPSHOP_GOODS_LIST.class); // [S_RESPONSE_NPSHOP_GOODS_LIST] (0x10C, captura Black Cloud Mail)
		addPacketOpcode(269, SM_NPSHOP_GOODS_RECV.class); // [S_RESPONSE_NPSHOP_GOODS_RECV] (0x10D, captura Black Cloud Mail)
		addPacketOpcode(270, S_SERVER_ENV.class); // [S_SERVER_ENV] (0x10E)
		addPacketOpcode(271, S_PROGRESS_ACHIEVEMENT.class); // [S_PROGRESS_ACHIEVEMENT] (0x10F)
		addPacketOpcode(273, S_CREATE_ACHIEVEMENT_EVENT.class); // [S_CREATE_ACHIEVEMENT_EVENT] (0x111)
		addPacketOpcode(276, S_ACHIEVEMENT_REWARD_NOTI.class); // [S_ACHIEVEMENT_REWARD_NOTI] (0x114)
		addPacketOpcode(277, S_CLEAR_ACHIEVEMENT_EVENT.class); // [S_CLEAR_ACHIEVEMENT_EVENT] (0x115)
		addPacketOpcode(278, S_BATTLEPASS_LIST.class); // [S_BATTLEPASS_LIST] (0x116)
		addPacketOpcode(279, S_BATTLEPASS_UPDATED.class); // [S_BATTLEPASS_UPDATED] (0x117)
		addPacketOpcode(281, S_GAMEPASS_INFO.class); // [S_GAMEPASS_INFO] (0x119)
		addPacketOpcode(282, S_GAMEPASS_OTHER_UPDATED.class); // [S_GAMEPASS_OTHER_UPDATED] (0x11A)
		addPacketOpcode(283, SM_QUNA.class); // [SM_QUNA] (0x11B)
		// 284/286 eram S_DISASSEMBLY_ITEMLIST/S_SELECT_DISASSEMBLY_ITEM_RESULT de outra versao; na 5.0 sao 0x104/0x105 (abaixo)
		addPacketOpcode(285, S_READY_ENTER_WORLD.class); // [S_READY_ENTER_WORLD] (0x11D)
		addPacketOpcode(288, SM_TUNE_RESULT.class); // [S_REIDENTIFY_PREVIEW]
		addPacketOpcode(290, SM_USER_CLASSIC_WARDROBE_LOAD.class); // [S_USER_CLASSIC_WARDROBE_LOAD] (0x122): 58 de 58 logins; 0x123 na lista 2.4
		addPacketOpcode(291, SM_USER_CLASSIC_WARDROBE_INFO_UPDATED.class); // [S_USER_CLASSIC_WARDROBE_INFO_UPDATED] (0x123): sem captura; 0x124 na 2.4
		addPacketOpcode(292, SM_USER_CLASSIC_WARDROBE_DATA_UPDATED.class); // [S_USER_CLASSIC_WARDROBE_DATA_UPDATED] (0x124): 5 de 5; 0x125 na 2.4
		addPacketOpcode(293, SM_AFTER_SIEGE_LOCINFO_475.class); // [S_ABYSS_INFO_GAB1_SPEC]
		addPacketOpcode(296, SM_BIND_POINT_TELEPORT.class); // [S_HOTSPOT]
		addPacketOpcode(298, SM_UPGRADE_ARCADE.class); // [S_GOTCHA_NOTIFY]
		// 299 SM_ATREIAN_PASSPORT removed: 4.8 retail residue not present in Classic 5.0
		addPacketOpcode(302, SM_LEGION_DOMINION_RANK.class); // [S_LEGION_DOMINION_RANKING]
		addPacketOpcode(303, SM_LOAD_EQUIPMENT_CHANGE.class); // [S_LOAD_EQUIPMENT_CHANGE] (0x12F)
		addPacketOpcode(289, SM_CHAT_ACCUSE.class); // [S_CHAT_ACCUSE] (0x121)
		addPacketOpcode(294, SM_SPAM_FILTER_FLAG.class); // [S_SPAM_FILTER_FLAG] (0x126)
		addPacketOpcode(300, SM_CHANNEL_CHATTING_BLACKLIST_SETTING.class); // [S_CHANNEL_CHATTING_BLACKLIST_SETTING] (0x12C)
		addPacketOpcode(307, SM_ENTER_WORLD_CHECK.class); // [S_ENTER_WORLD_CHECK] (0x133)
		addPacketOpcode(327, SM_SELL_ITEM.class); // [S_STORE_PURCHASE_INFO] (0x147)
		addPacketOpcode(415, S_DAEVA_PASS_DATA.class); // [S_DAEVA_PASS_DATA] (0x19F)
		addPacketOpcode(437, SM_RANKING_READY.class); // [S_UNK_01B5] (0x1B5)

		// 52 Classic 5.0 Opcodes mapped directly from official Wireshark PCAPs
		addPacketOpcode(95, SM_UNK_005F.class); // [S_UNK_005F] (0x005F)
		addPacketOpcode(146, SM_ENTER_WORLD_NOTIFY.class); // [S_ENTER_WORLD_NOTIFY] (0x0092)
		addPacketOpcode(188, SM_UNK_00BC.class); // [S_UNK_00BC] (0x00BC)
		addPacketOpcode(197, SM_UNK_00C5.class); // [S_UNK_00C5] (0x00C5)
		// Subida 1-60: 0x104 (212/95 b) logo apos o C_USE_ITEM de caixa selectable, 0x105 (9 b) depois do C_SELECT_DISASSEMBLY_ITEM
		addPacketOpcode(260, SM_FIRST_SHOW_DECOMPOSABLE.class); // [S_DISASSEMBLY_ITEMLIST] (0x0104)
		addPacketOpcode(261, SM_SECONDARY_SHOW_DECOMPOSABLE.class); // [S_SELECT_DISASSEMBLY_ITEM_RESULT] (0x0105)
		addPacketOpcode(265, SM_UNK_0109.class); // [S_UNK_0109] (0x0109)
		addPacketOpcode(272, SM_UNK_0110.class); // [S_UNK_0110] (0x0110)
		addPacketOpcode(275, SM_UNK_0113.class); // [S_UNK_0113] (0x0113)
		addPacketOpcode(295, SM_UNK_0127.class); // [S_UNK_0127] (0x0127)
		addPacketOpcode(297, SM_UNK_0129.class); // [S_UNK_0129] (0x0129)
		addPacketOpcode(304, SM_RANK_LIST.class); // [S_RANK_LIST] (0x0130)
		addPacketOpcode(305, SM_RANK_INFO.class); // [S_RANK_INFO] (0x0131)
		addPacketOpcode(309, SM_UNK_0135.class); // [S_UNK_0135] (0x0135)
		addPacketOpcode(312, SM_RANKING_BADGE.class); // [S_RANKING_BADGE] (0x0138)
		addPacketOpcode(314, SM_UNK_013A.class); // [S_UNK_013A] (0x013A)
		// Global Auction House 5.0 (capturas de 2026-09-11 a 13). A ordem dos nomes é a do enum S_GLOBAL_TRADE_* (LIST, MYLIST, BUY, COMMIT,
		// CANCEL, SALESLOG, COLLECT, AVG_PRICE, STATE, HISTORY), que casa com a função de todos os capturados a partir de 0x13C.
		addPacketOpcode(0x13C, SM_GLOBAL_TRADE_LIST.class); // [S_GLOBAL_TRADE_LIST]
		addPacketOpcode(0x13D, SM_GLOBAL_TRADE_MYLIST.class); // [S_GLOBAL_TRADE_MYLIST]
		addPacketOpcode(0x13E, SM_GLOBAL_TRADE_BUY.class); // [S_GLOBAL_TRADE_BUY]
		addPacketOpcode(0x13F, SM_GLOBAL_TRADE_COMMIT.class); // [S_GLOBAL_TRADE_COMMIT]
		addPacketOpcode(0x140, SM_GLOBAL_TRADE_CANCEL.class); // [S_GLOBAL_TRADE_CANCEL]
		addPacketOpcode(0x141, SM_GLOBAL_TRADE_SALESLOG.class); // [S_GLOBAL_TRADE_SALESLOG]
		addPacketOpcode(0x142, SM_GLOBAL_TRADE_COLLECT.class); // [S_GLOBAL_TRADE_COLLECT]
		addPacketOpcode(0x143, SM_GLOBAL_TRADE_AVG_PRICE.class); // [S_GLOBAL_TRADE_AVG_PRICE]
		addPacketOpcode(0x144, SM_GLOBAL_TRADE_STATE.class); // [S_GLOBAL_TRADE_STATE]
		addPacketOpcode(0x145, SM_GLOBAL_TRADE_HISTORY.class); // [S_GLOBAL_TRADE_HISTORY]
		// Altar of Transcendence 5.0: início e resultado da fusão (C 0x154)
		addPacketOpcode(0x1A6, SM_ITEM_COMPOSE_EVENT.class);
		addPacketOpcode(0x1A7, SM_ITEM_COMPOSE_RESULT.class);
		// Ascend (Item Upgrade) 5.0: início e resultado (C 0x106), captura Outros/outros_2026-09-21_06-10-28
		addPacketOpcode(0x1AD, SM_ITEM_UPGRADE_EVENT.class); // [S_ITEM_UPGRADE_EVENT]
		addPacketOpcode(0x1AE, SM_ITEM_UPGRADE_RESULT.class); // [S_ITEM_UPGRADE_RESULT]
		addPacketOpcode(326, SM_UNK_0146.class); // [S_UNK_0146] (0x0146)
		addPacketOpcode(328, SM_COMBAT_TALENT_REWARDS.class); // [S_COMBAT_POWER_REWARD_INFO] (0x0148)
		addPacketOpcode(329, SM_COMBAT_TALENT_REWARD_UPDATE.class); // [S_COMBAT_POWER_REWARD_UPDATE] (0x0149)
		addPacketOpcode(330, SM_UNK_014A.class); // [S_UNK_014A] (0x014A)
		addPacketOpcode(331, SM_SP_UPDATE.class); // SP do próprio Revenant (0x014B, 2 b)
		// Book of Legends 5.0 (captura 06_Sistemas_Novos_Book_of_Legends, 11/09): nomes do enum S_USER_STORY_BOOK_* do Game.dll
		addPacketOpcode(0x14C, SM_STORYBOOK_FINISHED_LIST.class); // [S_USER_STORY_BOOK_FINISHED_LIST_LOAD]
		addPacketOpcode(0x14D, SM_STORYBOOK_REGISTERED_LIST.class); // [S_USER_STORY_BOOK_REGISTERED_ITEM_LIST_LOAD]
		addPacketOpcode(0x14E, SM_STORYBOOK_UPDATE.class); // [S_USER_STORY_BOOK_UPDATE_RESULT], resposta ao C 0xE4
		addPacketOpcode(0x171, SM_STORYBOOK_APPRAISE_RESULT.class); // identificação de fragmentos, resposta ao C 0xDC
		addPacketOpcode(0x172, SM_STORYBOOK_DISASSEMBLE_RESULT.class); // desmontagem de fragmentos, resposta ao C 0xDD
		addPacketOpcode(337, SM_UNK_0151.class); // [S_UNK_0151] (0x0151)
		addPacketOpcode(338, SM_UNK_0152.class); // [S_UNK_0152] (0x0152)
		addPacketOpcode(342, SM_LEGION_DONATION_MEMBERS.class); // pontos de produção por membro (0x0156)
		addPacketOpcode(343, SM_LEGION_DONATION_POINTS.class); // pontos de produção da Legion no dia (0x0157)
		addPacketOpcode(344, SM_LEGION_DONATION_STATUS.class); // produções hoje e dias seguidos (0x0158)
		addPacketOpcode(345, SM_LEGION_DONATION_LIST.class); // lista de produção do dia (0x0159)
		addPacketOpcode(346, SM_LEGION_CRAFT_LIST.class); // receitas de produção da Legion (0x015A)
		addPacketOpcode(348, SM_UNK_015C.class); // [S_UNK_015C] (0x015C)
		addPacketOpcode(350, SM_UNK_015E.class); // [S_UNK_015E] (0x015E)
		addPacketOpcode(357, SM_LEGION_COIN.class); // moedas pessoais da Legion (0x0165)
		addPacketOpcode(358, SM_SP_UPDATE_OTHER.class); // SP de um jogador para quem o vê (0x0166, 6 b)
		addPacketOpcode(0x169, SM_MOROS_INFO.class); // Moreth, Chronicle of Time: [H nível][D pontos][D 0][H registros] (40 de 40 capturas)
		addPacketOpcode(368, SM_UNK_0170.class); // [S_UNK_0170] (0x0170)
		addPacketOpcode(371, SM_UNK_0173.class); // [S_UNK_0173] (0x0173)
		addPacketOpcode(373, SM_EP_UPDATE.class); // EP (Ki) do próprio Brawler (0x0175, 2 b)
		addPacketOpcode(374, SM_EP_UPDATE_OTHER.class); // EP de um jogador para quem o vê (0x0176, 6 b)
		addPacketOpcode(375, SM_UNK_0177.class); // [S_UNK_0177] (0x0177)
		addPacketOpcode(383, SM_PROTOCOL_VERSION.class); // [S_PROTOCOL_VERSION] (0x017F)
		addPacketOpcode(384, SM_WORLD_VARIABLE.class); // [S_WORLD_VARIABLE] (0x0180) — variaveis de mundo do mapa
		addPacketOpcode(385, SM_UNK_0181.class); // [S_UNK_0181] (0x0181)
		addPacketOpcode(386, SM_UNK_0182.class); // [S_UNK_0182] (0x0182)
		addPacketOpcode(387, SM_UNK_0183.class); // [S_UNK_0183] (0x0183)
		addPacketOpcode(391, SM_CAMP_PVP_ZONE.class); // [S_ZONE_PVP] (0x0187) — zona PvP das torres de Tiamaranta
		addPacketOpcode(396, SM_UNK_018C.class); // [S_UNK_018C] (0x018C)
		addPacketOpcode(401, SM_UNK_0191.class); // [S_UNK_0191] (0x0191)
		addPacketOpcode(407, SM_UNK_0197.class); // [S_UNK_0197] (0x0197)
		addPacketOpcode(413, SM_ZONE_STATE_LIST.class); // [S_ZONE_STATE_LIST] (0x019D) — lista de zonas do mapa na entrada
		// SM_UNK_019D saiu: era um blob fixo com zonas DF4_* de outro mapa e nunca era enviado
		addPacketOpcode(424, SM_UNK_01A8.class); // [S_UNK_01A8] (0x01A8)
		addPacketOpcode(426, SM_UNK_01AA.class); // [S_UNK_01AA] (0x01AA)
		addPacketOpcode(427, SM_UNK_01AB.class); // [S_UNK_01AB] (0x01AB)
		addPacketOpcode(428, SM_UNK_01AC.class); // [S_UNK_01AC] (0x01AC)
		addPacketOpcode(431, SM_UNK_01AF.class); // [S_UNK_01AF] (0x01AF)
		addPacketOpcode(435, SM_UNK_01B3.class); // [S_UNK_01B3] (0x01B3)
		addPacketOpcode(442, SM_UNK_01BA.class); // [S_UNK_01BA] (0x01BA)
		addPacketOpcode(445, SM_UNK_01BD.class); // [S_UNK_01BD] (0x01BD)
		addPacketOpcode(448, SM_UNK_01C0.class); // [S_UNK_01C0] (0x01C0)
		addPacketOpcode(450, SM_UNK_01C2.class); // [S_UNK_01C2] (0x01C2)
		addPacketOpcode(453, SM_UNK_01C5.class); // [S_UNK_01C5] (0x01C5)
		addPacketOpcode(0x1A3, SM_SIEL_ANVIL_START.class);
		addPacketOpcode(0x1C3, SM_CLASSIC_ENCHANT_ANIMATION.class);
		addPacketOpcode(0x1A4, SM_SIEL_ANVIL_RESULT.class);
		addPacketOpcode(0x1C4, SM_SIEL_HAMMER_EVENT.class);
		addPacketOpcode(0x1A2, SM_SIEL_HAMMER_RESULT.class);
		addPacketOpcode(363, SM_ALTER_INFO.class); // [S_ALTER_INFO] (0x016B)
	}

	static int getOpcode(Class<? extends AionServerPacket> packetClass) {
		Integer opcode = opcodes.get(packetClass);
		if (opcode == null) {
			// subclasse nao registrada (ex.: S_MOVE_NEW) usa o opcode do ancestral registrado mais proximo; o mapa e consultado
			// por varias threads ao mesmo tempo, entao nada de iterar e gravar num HashMap (CME no MoveTaskManager)
			for (Class<?> c = packetClass.getSuperclass(); c != null && opcode == null; c = c.getSuperclass())
				opcode = opcodes.get(c);
			if (opcode == null)
				throw new IllegalArgumentException("There is no opcode for " + packetClass + " defined.");
			opcodes.putIfAbsent(packetClass, opcode);
		}

		return opcode;
	}

	private static void addPacketOpcode(int opcode, Class<? extends AionServerPacket> packetClass) {
		if (opcode < 0)
			return;

		if (opcodes.values().contains(opcode))
			throw new IllegalArgumentException(String.format("There already exists another packet with id 0x%02X", opcode));

		opcodes.put(packetClass, opcode);
	}

}
