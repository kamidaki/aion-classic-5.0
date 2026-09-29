package com.aionemu.gameserver.network.factories;

import java.lang.reflect.Constructor;
import java.util.EnumSet;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.AionPacketHandler;
import com.aionemu.gameserver.network.aion.clientpackets.*;

public class AionPacketHandlerFactory {

	private static final Logger log = LoggerFactory.getLogger(AionPacketHandlerFactory.class);

	private final AionPacketHandler handler;

	public static AionPacketHandlerFactory getInstance() {
		return SingletonHolder.instance;
	}

	public AionPacketHandlerFactory() {
		handler = new AionPacketHandler();

		// ==========================================
		// CONNECTED / AUTH HANDSHAKE (5.0 Classic)
		// ==========================================
		addPacket(CM_VERSION_CHECK.class, 0xF2, State.CONNECTED); // 0x0000 VERSION
		addPacket(CM_TIME_CHECK.class, 0xE0, State.CONNECTED, State.AUTHED, State.IN_GAME); // 0x0012 SYNC_TIME
		addPacket(CM_L2AUTH_LOGIN_CHECK.class, 0x182, State.CONNECTED); // 0x00F0 HQ_LOGIN
		addPacket(CM_L2AUTH_LOGIN_CHECK.class, 0x117, State.CONNECTED); // 0x005D L2AUTH_LOGIN
		addPacket(CM_L2AUTH_LOGIN_CHECK.class, 0x11F, State.CONNECTED); // Legacy fallback
		addPacket(CM_AUTH_SUCCESS.class, 0x00E2, State.AUTHED); // 0x00E2 READY_ENTER_WORLD_ACK (AUTHED)
		addPacket(CM_AUTH_SUCCESS.class, 0x190, State.AUTHED, State.IN_GAME); // 0x0190
		addPacket(CM_AUTH_SUCCESS.class, 0x193, State.AUTHED, State.IN_GAME); // Legacy fallback
		addPacket(CM_LEGION_SEND_EMBLEM_INFO.class, 0x00E2, State.IN_GAME); // 0x00E2 C_REQUEST_GUILD_NAME (IN_GAME)
		addPacket(CM_LEGION_SEND_EMBLEM_INFO.class, 0x10, State.IN_GAME); // Raw alias
		addPacket(CM_MAC_ADDRESS.class, 0x1AC, State.CONNECTED, State.AUTHED, State.IN_GAME); // 0x00D6 MACHINE_INFO
		addPacket(CM_MAC_ADDRESS.class, 0x174, State.CONNECTED, State.AUTHED, State.IN_GAME); // Legacy fallback

		// ==========================================
		// CHARACTER SELECTION & LOBBY (5.0 Classic)
		// ==========================================
		addPacket(CM_CHARACTER_LIST.class, 0x114, State.AUTHED); // 0x005E SESSION_KEY_ECHO
		addPacket(CM_CHARACTER_LIST.class, 0x11C, State.AUTHED); // Legacy fallback
		addPacket(CM_CREATE_CHARACTER.class, 0x115, State.AUTHED); // 0x005F CREATE_CHARACTER
		addPacket(CM_CREATE_CHARACTER.class, 0x11D, State.AUTHED); // Legacy fallback
		addPacket(CM_DELETE_CHARACTER.class, 0x11A, State.AUTHED); // 0x011A WIRE DELETE_CHARACTER (dec=0x0068)
		addPacket(CM_DELETE_CHARACTER.class, 0x68, State.AUTHED); // Raw alias
		addPacket(CM_RESTORE_CHARACTER.class, 0x11B, State.AUTHED); // 0x011B WIRE RESTORE_CHARACTER (dec=0x0069)
		addPacket(CM_RESTORE_CHARACTER.class, 0x69, State.AUTHED); // Raw alias
		addPacket(CM_CHARACTER_EDIT.class, 0xED, State.AUTHED); // 0x0017 CHARACTER_EDIT
		addPacket(CM_CHECK_NICKNAME.class, 0x143, State.AUTHED); // 0x00B1 CHECK_NICKNAME
		addPacket(CM_CHECK_NICKNAME.class, 0xB1, State.AUTHED); // Raw alias
		addPacket(CM_MAY_LOGIN_INTO_GAME.class, 0x179, State.AUTHED, State.IN_GAME); // 0x008B SA_ACCOUNT_ITEM_QUERY
		addPacket(CM_MAY_LOGIN_INTO_GAME.class, 0x8B, State.AUTHED, State.IN_GAME); // Raw alias
		addPacket(CM_ENTER_WORLD.class, 0xEA, State.AUTHED); // 0x0018 ENTER_WORLD
		addPacket(CM_ENTER_WORLD.class, 0x18, State.AUTHED); // Raw alias
		addPacket(CM_CHARACTER_PASSKEY.class, 0x1A0, State.AUTHED); // 0x00D2 SECOND_PASSWORD
		addPacket(CM_CHARACTER_PASSKEY.class, 0xD2, State.AUTHED); // Raw alias
		addPacket(CM_MAY_QUIT.class, 0xFE, State.AUTHED, State.IN_GAME); // 0x0004 READY_TO_QUIT
		addPacket(CM_MAY_QUIT.class, 0xEE, State.AUTHED, State.IN_GAME); // Legacy fallback
		addPacket(CM_MAY_QUIT.class, 0x04, State.AUTHED, State.IN_GAME); // Raw alias
		addPacket(CM_QUIT.class, 0xF1, State.AUTHED, State.IN_GAME); // 0x0003 ASK_QUIT
		addPacket(CM_SHOW_BLOCKLIST.class, 0x14A, State.IN_GAME); // 0x00B8 SHOW_BLOCKLIST
		addPacket(CM_SHOW_BLOCKLIST.class, 0x15A, State.IN_GAME); // 0x00A8 C_QUERY_BLOCK (5.0 Classic)
		addPacket(CM_RECONNECT_AUTH.class, 0x17A, State.AUTHED); // Legacy fallback
		addPacket(CM_PING.class, 0xC6, State.AUTHED, State.IN_GAME); // 0x002C ALIVE / PING
		addPacket(CM_PING.class, 0x22B, State.AUTHED, State.IN_GAME); // 0x0159 PING_159

		// ==========================================
		// IN-GAME WORLD & GAMEPLAY (5.0 Classic)
		// ==========================================
		addPacket(CM_LEVEL_READY.class, 0xEB, State.AUTHED, State.IN_GAME); // 0x0019 C_LEVEL_READY (5.0 Classic)
		addPacket(CM_LEVEL_READY.class, 0x19, State.AUTHED, State.IN_GAME); // Alias dec opcode
		addPacket(CM_LEVEL_READY.class, 0x09, State.AUTHED, State.IN_GAME); // Alias 4.8 opcode
		addPacket(CM_UI_SETTINGS.class, 0xE8, State.IN_GAME); // 0x001A UI_SETTINGS
		addPacket(CM_CHAT_MESSAGE_PUBLIC.class, 0xE9, State.IN_GAME); // 0x001B CHAT_MESSAGE_PUBLIC
		addPacket(CM_CHAT_MESSAGE_PUBLIC.class, 0x99, State.IN_GAME); // Legacy fallback
		addPacket(CM_CHAT_MESSAGE_WHISPER.class, 0xD6, State.IN_GAME); // 0x001C CHAT_MESSAGE_WHISPER
		addPacket(CM_CHAT_MESSAGE_WHISPER.class, 0x96, State.IN_GAME); // Legacy fallback
		addPacket(CM_ATTACK.class, 0xD2, State.IN_GAME); // 0x0020 ATTACK
		addPacket(CM_CASTSPELL.class, 0xD3, State.IN_GAME); // 0x0021 USE_SKILL
		addPacket(CM_TOGGLE_SKILL_DEACTIVATE.class, 0xD0, State.IN_GAME); // 0x0022 TOGGLE_SKILL
		addPacket(CM_REMOVE_ALTERED_STATE.class, 0xD1, State.IN_GAME); // 0x0027 REMOVE_BUFF
		addPacket(CM_USE_ITEM.class, 0xC7, State.IN_GAME); // 0x002D USE_ITEM
		addPacket(CM_USE_ITEM.class, 0xCF, State.IN_GAME); // Legacy fallback
		addPacket(CM_EQUIP_ITEM.class, 0xC4, State.IN_GAME); // 0x002E USE_EQUIPMENT_ITEM
		addPacket(CM_EQUIP_ITEM.class, 0xCC, State.IN_GAME); // Legacy fallback
		addPacket(CM_MOVE.class, 0xC2, State.IN_GAME); // 0x0030 MOVE_NEW
		addPacket(CM_MOVE_IN_AIR.class, 0xC3, State.IN_GAME); // 0x0031 PATH_FLY
		addPacket(CM_QUESTION_RESPONSE.class, 0xC0, State.IN_GAME); // 0x0032 QUESTION_RESPONSE
		addPacket(CM_BUY_ITEM.class, 0xC1, State.IN_GAME); // 0x0033 BUY_SELL
		addPacket(CM_TARGET_SELECT.class, 0xCD, State.IN_GAME); // 0x0037 CHANGE_TARGET
		addPacket(CM_TARGET_SELECT.class, 0x95, State.IN_GAME); // Legacy fallback
		addPacket(CM_PLAYER_LISTENER.class, 0xCA, State.IN_GAME); // 0x0038 MOVE_OBJECT
		addPacket(CM_BUILDER_COMMAND.class, 0xC8, State.IN_GAME); // 0x003A GM_COMMAND
		addPacket(CM_EMOTION.class, 0xC9, State.IN_GAME); // 0x003B EMOTION
		addPacket(CM_REMOVE_STIGMA.class, 0x136, State.IN_GAME); // 0x003C REMOVE_STIGMA / DESTROY_ITEM ([D itemObjId], distinguished by equipped state)
		addPacket(CM_BROKER_REGISTERED.class, 0x137, State.IN_GAME); // 0x003D BROKER_REGISTERED
		addPacket(CM_BUY_BROKER_ITEM.class, 0x134, State.IN_GAME); // 0x003E BUY_BROKER_ITEM
		addPacket(CM_REGISTER_BROKER_ITEM.class, 0x135, State.IN_GAME); // 0x003F REGISTER_BROKER_ITEM
		addPacket(CM_EXCHANGE_ADD_ITEM.class, 0x132, State.IN_GAME); // 0x0040 EXCHANGE_ADD_ITEM
		addPacket(CM_EXCHANGE_ADD_KINAH.class, 0x130, State.IN_GAME); // 0x0042 EXCHANGE_ADD_KINAH
		addPacket(CM_EXCHANGE_LOCK.class, 0x131, State.IN_GAME); // 0x0043 EXCHANGE_LOCK
		addPacket(CM_EXCHANGE_CANCEL.class, 0x12F, State.IN_GAME); // 0x0055 EXCHANGE_CANCEL
		addPacket(CM_EXCHANGE_OK.class, 0x12E, State.IN_GAME); // 0x0054 EXCHANGE_OK
		// O cru 0xF5 (dec 0xFFFF) na 5.0 é [D página][C aba 0..3], o pedido de histórico da Legion (respondido com o S 0x0C da aba), e não pedido de
		// troca: o CM_EXCHANGE_REQUEST respondia "no one to trade with" a cada um. O pedido de troca da 5.0 não aparece em nenhuma captura.
		addPacket(CM_LEGION_HISTORY.class, 0xF5, State.IN_GAME); // 0xFFFF C_REQUEST_GUILD_HISTORY
		addPacket(CM_INIT_LEVEL.class, 0x12C, State.IN_GAME); // 0x0056 INIT_LEVEL (5.0 Classic)
		addPacket(CM_PRIVATE_STORE.class, 0x13D, State.IN_GAME); // 0x0047 PRIVATE_STORE
		addPacket(CM_PRIVATE_STORE_NAME.class, 0x13A, State.IN_GAME); // 0x0048 PRIVATE_STORE_NAME
		addPacket(CM_SUMMON_COMMAND.class, 0x13B, State.IN_GAME); // 0x0049 SUMMON_COMMAND
		addPacket(CM_BROKER_LIST.class, 0x139, State.IN_GAME); // 0x004B BROKER_LIST
		addPacket(CM_LEGION_WH_KINAH.class, 0x126, State.IN_GAME); // 0x004C GUILD_WH_KINAH
		addPacket(CM_PLAY_MOVIE_END.class, 0x123, State.IN_GAME); // 0x0051 PLAY_MOVIE_END
		addPacket(CM_PLAYER_STATUS_INFO.class, 0x112, State.IN_GAME); // 0x0060 PARTY
		addPacket(CM_INVITE_TO_GROUP.class, 0x113, State.IN_GAME); // 0x0061 PARTY_BY_NAME
		addPacket(CM_START_LOOT.class, 0x118, State.IN_GAME); // 0x006A LOOT
		addPacket(CM_LOOT_ITEM.class, 0x119, State.IN_GAME); // 0x006B LOOT_ITEM
		addPacket(CM_GROUP_DISTRIBUTION.class, 0x106, State.IN_GAME); // 0x006C GROUP_DISTRIBUTION
		addPacket(CM_SHOW_FRIENDLIST.class, 0x104, State.IN_GAME); // 0x006E QUERY_BUDDY
		addPacket(CM_FRIEND_ADD.class, 0x105, State.IN_GAME); // 0x006F ADD_BUDDY
		addPacket(CM_FRIEND_DEL.class, 0x102, State.IN_GAME); // 0x0070 FRIEND_DEL
		addPacket(CM_DUEL_REQUEST.class, 0x100, State.IN_GAME); // 0x0072 DUEL_REQUEST
		addPacket(CM_VIEW_PLAYER_DETAILS.class, 0x10E, State.IN_GAME); // 0x0074 VIEW_PLAYER_DETAILS
		addPacket(CM_GAMEGUARD.class, 0x10A, State.IN_GAME); // 0x0078 GG
		addPacket(CM_CLIENT_COMMAND_ROLL.class, 0x109, State.IN_GAME); // 0x007B ROLL
		addPacket(CM_BROKER_CANCEL_REGISTERED.class, 0x172, State.IN_GAME); // 0x0080 BROKER_CANCEL
		addPacket(CM_BROKER_SETTLE_LIST.class, 0x173, State.IN_GAME); // 0x0081 BROKER_SETTLE_LIST
		addPacket(CM_BROKER_SETTLE_ACCOUNT.class, 0x170, State.IN_GAME); // 0x0082 BROKER_SETTLE_ACCOUNT
		addPacket(CM_SHOW_BRAND.class, 0x17F, State.IN_GAME); // 0x0085 SHOW_BRAND
		addPacket(CM_CHAT_AUTH.class, 0x17C, State.IN_GAME); // 0x0086 SIGN_CLIENT
		addPacket(CM_GROUP_LOOT.class, 0x17B, State.IN_GAME); // 0x0089 GROUP_LOOT
		addPacket(CM_DISTRIBUTION_SETTINGS.class, 0x178, State.IN_GAME); // 0x008A DISTRIBUTION_SETTINGS
		// 0x008D não é C_COMBINE na 5.0: é o C_MAIL_LIST (1 b, respondido pelo S_MAIL tipo 2) nas capturas Black Cloud Mail e express.
		// O opcode do C_COMBINE na 5.0 ainda não apareceu em captura.
		// addPacket(CM_CRAFT.class, 0x167, State.IN_GAME);
		addPacket(CM_SIEL_ANVIL.class, 0x1FA, State.IN_GAME); // decoded 0x0108 Siel Anvil, Classic 5.0
		addPacket(CM_SIEL_ANVIL_CANCEL.class, 0x1FB, State.IN_GAME);
		addPacket(CM_SIEL_HAMMER.class, 0x1F5, State.IN_GAME);
		addPacket(CM_SIEL_HAMMER_CANCEL.class, 0x220, State.IN_GAME);
		addPacket(CM_SEND_MAIL.class, 0x17E, State.IN_GAME); // 0x0084 SEND_MAIL
		addPacket(CM_CHECK_MAIL_LIST.class, 0x167, State.IN_GAME); // 0x008D C_MAIL_LIST (5.0 Classic: [C só expresso], captura Black Cloud Mail)
		addPacket(CM_READ_MAIL.class, 0x164, State.IN_GAME); // 0x008E C_MAIL_READ (5.0 Classic: [D carta], respondido pelo S_MAIL tipo 3)
		addPacket(CM_GET_MAIL_ATTACHMENT.class, 0x16A, State.IN_GAME); // 0x0098 GET_MAIL_ATTACHMENT
		addPacket(CM_DELETE_MAIL.class, 0x16B, State.IN_GAME); // 0x0099 DELETE_MAIL
		addPacket(CM_READ_EXPRESS_MAIL.class, 0x150, State.IN_GAME); // 0x00A2 READ_EXPRESS_MAIL
		// 0x00A9 é a escolha da caixa selectable, não BLACKCLOUD_MAIL_OPEN: nas capturas só aparece (4x, 9 b [obj][0][índice]) logo depois do S 0x104
		addPacket(CM_SELECT_DECOMPOSABLE.class, 0x15B, State.IN_GAME); // 0x00A9 C_SELECT_DISASSEMBLY_ITEM
		addPacket(CM_NPSHOP_GOODS_LIST.class, 0x157, State.IN_GAME); // 0x009D C_SA_GOODSLIST (Black Cloud Mail, sem corpo)
		addPacket(CM_NPSHOP_GOODS_RECV.class, 0x154, State.IN_GAME); // 0x009E C_SA_CONFIRMGOODS (Black Cloud Mail, [Q mercadoria])
		addPacket(CM_NPSHOP_GOODS_COUNT.class, 0x158, State.IN_GAME); // 0x00AA C_REQUEST_NPSHOP_GOODS_COUNT (sempre seguido do S 0x10A nas capturas)
		addPacket(CM_REPLACE_ITEM.class, 0x140, State.IN_GAME); // 0x00B2 REPLACE_ITEM
		addPacket(CM_BLOCK_SET_REASON.class, 0x141, State.IN_GAME); // 0x00B3 BLOCK_SET_REASON
		addPacket(CM_MOVE_ITEM.class, 0x14E, State.IN_GAME); // 0x00B4 MOVE_ITEM (5.0 Classic: [D obj][C origem][C destino][H slot], 366 pacotes de 8 b nas capturas)
		addPacket(CM_BLOCK_DEL.class, 0x14D, State.IN_GAME); // 0x00B7 BLOCK_DEL
		addPacket(CM_FRIEND_STATUS.class, 0x148, State.IN_GAME); // 0x00BA FRIEND_STATUS
		addPacket(CM_INSTANCE_INFO.class, 0x1B3, State.IN_GAME); // 0x00C1 INSTANCE_DUNGEON_COOLTIMES
		addPacket(CM_BOARD_BUSINESS.class, 0x1BE, State.IN_GAME); // 0x00C4 BOARD_BUSINESS
		addPacket(CM_QUEST_TELEPORT.class, 0x1B4, State.IN_GAME); // 0x00BE C_REQUEST_TELEPORT_TO_NPC (5.0 Classic Quest Teleport Icon)
		addPacket(CM_QUEST_TELEPORT.class, 0x00BE, State.IN_GAME); // Raw alias dec 0x00BE
		addPacket(CM_QUEST_TELEPORT.class, 0x1BF, State.IN_GAME); // 0x00C5 REQUEST_GUILD_HISTORY / Legacy fallback
		addPacket(CM_SUMMON_ATTACK.class, 0x15E, State.IN_GAME); // 0x00A4 SUMMON_ATTACK (5.0 Classic: [D summon][D alvo][C][H tempo][C], 43 pacotes de 12 b nas capturas do Spirit Master)
		addPacket(CM_SUMMON_CASTSPELL.class, 0x15C, State.IN_GAME); // 0x00A6 SUMMON_CASTSPELL (5.0 Classic: [D summon][H skill][C 1][D alvo][F], 25 pacotes de 15 b)
		addPacket(CM_SHOW_MAP.class, 0x1AF, State.AUTHED, State.IN_GAME); // 0x00D5 SHOW_MAP (5.0: [C 0] logo depois do C_ENTER_WORLD, antes do LEVEL_READY)
		addPacket(CM_AUTO_GROUP.class, 0x1AB, State.IN_GAME); // 0x00D9 AUTO_GROUP
		addPacket(CM_SUMMON_MOVE.class, 0x1A8, State.IN_GAME); // 0x00DA SUMMON_MOVE
		addPacket(CM_SUMMON_EMOTION.class, 0x1A9, State.IN_GAME); // 0x00DB SUMMON_EMOTION
		addPacket(CM_CUSTOM_SETTINGS.class, 0xE6, State.IN_GAME); // 0x000C CUSTOM_SETTINGS
		addPacket(CM_CAPTCHA.class, 0xE4, State.IN_GAME); // 0x000E CAPTCHA
		addPacket(CM_SET_NOTE.class, 0xF8, State.IN_GAME); // 0x000A SAVE_CLIENT_SETTINGS
		addPacket(CM_DIALOG_SELECT.class, 0xF4, State.IN_GAME); // 0xFFFE DIALOG_SELECT
		addPacket(CM_TELEPORT_ANIMATION_DONE.class, 0x9D, State.IN_GAME); // 0xFFE7 TELEPORT_ANIMATION_DONE
		addPacket(CM_TITLE_SET.class, 0x169, State.IN_GAME); // 0x009B TITLE_SET
		addPacket(CM_QUESTIONNAIRE.class, 0x163, State.IN_GAME); // 0x0091 QUESTIONNAIRE
		// MOVE_ITEM e SPLIT_ITEM da 5.0 sao dec 0x00B4/0x00B5 (registrados acima e abaixo); dec 0x009C/0x009D nunca aparecem nas capturas
		addPacket(CM_DELETE_QUEST.class, 0x122, State.IN_GAME); // DELETE_QUEST
		// C_DEAD_RESTART na 5.0 é dec 0x000D [C tipo]: 7 de 7 nas capturas, sempre depois do S_RESURRECT_INFO (0xC0) e seguido da ressurreição.
		// O dec 0x0005 da 4.8 é outro pacote na 5.0 (7 b, 08 00 00 00 00 00 00, um por sessão), que o CM_REVIVE lia como revive no obelisco.
		addPacket(CM_REVIVE.class, 0xE7, State.IN_GAME); // 0x000D C_DEAD_RESTART (5.0 Classic)
		// C_GUILD: [C 08][D 0][H 0] -> S_GUILD_INFO depois de cada troca de mapa (83 de 100). Criar, convidar, cargo e aviso conferidos na
		// criação da Lost Academy (22/09 10:23); ver CM_LEGION.
		addPacket(CM_LEGION.class, 0x00FF, State.IN_GAME); // 0x0005 C_GUILD
		addPacket(CM_REVIVE.class, 0x0005, State.IN_GAME); // Raw alias
		addPacket(CM_REVIVE.class, 0xEF, State.IN_GAME); // Legacy fallback
		addPacket(CM_TELEPORT_SELECT.class, 0x116, State.IN_GAME); // 0x005C TELEPORT_SELECT (5.0 Classic wire)
		addPacket(CM_TELEPORT_SELECT.class, 0x005C, State.IN_GAME); // Raw alias dec 0x005C
		addPacket(CM_TELEPORT_SELECT.class, 0x16E, State.IN_GAME); // 0x0094 TELEPORT_SELECT (Flight & Teleport NPCs)
		addPacket(CM_TELEPORT_SELECT.class, 0x0094, State.IN_GAME); // Raw alias
		addPacket(CM_PLAYER_SEARCH.class, 0x155, State.IN_GAME); // PLAYER_SEARCH (0x155 Who Key 'V')
		addPacket(CM_MOTION.class, 0x12D, State.IN_GAME); // MOTION
		addPacket(CM_FUSION_WEAPONS.class, 0x1A5, State.IN_GAME); // FUSION_WEAPONS
		addPacket(CM_BREAK_WEAPONS.class, 0x1A2, State.IN_GAME); // BREAK_WEAPONS
		addPacket(CM_PET.class, 0x9C, State.IN_GAME); // PET
		addPacket(CM_PET_EMOTE.class, 0x9E, State.IN_GAME); // PET_EMOTE
		addPacket(CM_CUBE_EXPAND.class, 0x1B8, State.IN_GAME); // decoded 0x00CA CUBE_EXPAND (Classic 5.0: [C type], no NPC id)
		addPacket(CM_COMBAT_TALENT_REWARD.class, 0x1E5, State.IN_GAME); // decoded 0x010F [H rewardId]
		addPacket(CM_MANASTONE.class, 0x128, State.IN_GAME); // MANASTONE / ENCHANMENT_STONES
		addPacket(CM_GODSTONE_SOCKET.class, 0x2D9, State.IN_GAME); // 0x022B GIVE_ITEM_PROC
		addPacket(CM_GODSTONE_CLEAR.class, 0x1F9, State.IN_GAME); // 0x010B GIVE_ITEM_PROC_CLEAR
		addPacket(CM_GATHER.class, 0xE1, State.IN_GAME); // GATHER
		addPacket(CM_MACRO_DELETE.class, 0x142, State.IN_GAME); // MACRO_DELETE
		addPacket(CM_MACRO_CREATE.class, 0x145, State.IN_GAME); // MACRO_CREATE
		addPacket(CM_ABYSS_RANKING_PLAYERS.class, 0x177, State.IN_GAME); // ABYSS_RANKING_PLAYERS
		addPacket(CM_WINDSTREAM.class, 0x13C, State.IN_GAME); // 0x0046 WIND_PATH / WINDSTREAM
		addPacket(CM_CHARGE_ITEM.class, 0x124, State.IN_GAME); // CHARGE_ITEM
		addPacket(CM_GUILD_JOIN_REQUEST.class, 0x1EA, State.IN_GAME); // GUILD_JOIN_REQUEST
		addPacket(CM_GUILD_JOIN_CANCEL.class, 0x1EB, State.IN_GAME); // GUILD_JOIN_CANCEL
		// [D Legion] -> S_GUILD_EMBLEM_IMG_BEGIN + S_GUILD_EMBLEM_IMG_DATA (12 de 12; 22/09 16:14 e 10:23). Aqui ficava um CM_GUILD_TABS vazio.
		addPacket(CM_LEGION_SEND_EMBLEM.class, 0xFD, State.IN_GAME); // 0x0007 C_REQUEST_GUILD_EMBLEM_IMG
		addPacket(CM_EQUIPMENT_CHANGE.class, 0x182, State.IN_GAME); // EQUIPMENT_CHANGE
		addPacket(CM_EQUIPMENT_CHANGE_USE.class, 0x183, State.IN_GAME); // EQUIPMENT_CHANGE_USE
		// Wardrobe 5.0: capturas 06_Sistemas_Novos_5.0 de 2026-09-21 14:56 e 15:16. A 2.4/2.7 tinha REGISTER..EXTEND seguidos em 0xF5-0xFA.
		addPacket(CM_USER_CLASSIC_WARDROBE_REGISTER.class, 0x184, State.IN_GAME); // 0x00EE [D item] (1 de 1)
		addPacket(CM_USER_CLASSIC_WARDROBE_REMOVE.class, 0x185, State.IN_GAME); // 0x00EF [D entrada] (2 de 2)
		addPacket(CM_USER_CLASSIC_WARDROBE_DYE.class, 0x18A, State.IN_GAME); // 0x00F8 [D entrada][D tinta] (1 de 1)
		addPacket(CM_USER_CLASSIC_WARDROBE_FAVORITE.class, 0x18B, State.IN_GAME); // 0x00F9 [D entrada][C 1] (1 de 1)
		addPacket(CM_USER_CLASSIC_WARDROBE_APPLY.class, 0x188, State.IN_GAME); // 0x00FA [D item][D entrada ou 0] (5 de 5)
		addPacket(CM_USER_CLASSIC_WARDROBE_EXTEND.class, 0x189, State.IN_GAME); // 0x00FB [H 1][C 1 Quna, 2 item]: sem captura, conferido no cliente em 21/09
		addPacket(CM_RECIPE_LIST.class, 0x14C, State.AUTHED, State.IN_GAME); // 0x00B6 RECIPE_LIST (5.0 Classic)
		addPacket(CM_RECIPE_LIST.class, 0xB6, State.AUTHED, State.IN_GAME); // Alias dec opcode
		// Global Auction House 5.0 (capturas de 2026-09-11 a 21). O 0x1ED tinha o CM_GUILD_SEARCH da 4.x, sem ação.
		addPacket(CM_GLOBAL_TRADE_CANCEL.class, 0x1F2, State.IN_GAME); // 0x0100 C_GLOBAL_TRADE_CANCEL [Q anúncio]
		addPacket(CM_GLOBAL_TRADE_SALESLOG.class, 0x1F3, State.IN_GAME); // 0x0101 C_GLOBAL_TRADE_SALESLOG [C][C][C moeda][C][H]
		addPacket(CM_GLOBAL_TRADE_COLLECT.class, 0x1F0, State.IN_GAME); // 0x0102 C_GLOBAL_TRADE_COLLECT [D moeda]
		addPacket(CM_GLOBAL_TRADE_AVG_PRICE.class, 0x1F1, State.IN_GAME); // 0x0103 C_GLOBAL_TRADE_AVG_PRICE [D objeto][D moeda]
		addPacket(CM_GLOBAL_TRADE_STATE.class, 0x1E6, State.IN_GAME); // 0x010C C_GLOBAL_TRADE_STATE, sem corpo, ao abrir a janela
		addPacket(CM_GLOBAL_TRADE_HISTORY.class, 0x1E7, State.IN_GAME); // 0x010D C_GLOBAL_TRADE_HISTORY [C][C][C moeda][C][H]
		addPacket(CM_GLOBAL_TRADE_LIST.class, 0x1EE, State.IN_GAME); // 0x0114 C_GLOBAL_TRADE_LIST
		addPacket(CM_GLOBAL_TRADE_MYLIST.class, 0x1EF, State.IN_GAME); // 0x0115 C_GLOBAL_TRADE_MYLIST [D moeda]
		addPacket(CM_GLOBAL_TRADE_BUY.class, 0x1EC, State.IN_GAME); // 0x0116 C_GLOBAL_TRADE_BUY [Q anúncio]
		addPacket(CM_GLOBAL_TRADE_COMMIT.class, 0x1ED, State.IN_GAME); // 0x0117 C_GLOBAL_TRADE_COMMIT [D objeto][Q preço][Q qtd][D moeda]
		addPacket(CM_ITEM_COMPOSE.class, 0x22E, State.IN_GAME); // 0x0154 Altar of Transcendence [D receita][H n][n x (D item, D qtd)][D 0][C fusões]
		addPacket(CM_ITEM_UPGRADE.class, 0x1FC, State.IN_GAME); // 0x0106 Ascend [D receita][D objeto][D opção]
		addPacket(CM_ITEM_UPGRADE_CANCEL.class, 0x230, State.IN_GAME); // 0x0142 C_CANCEL_ITEM_UPGRADE [D itemId]
		addPacket(CM_MOROS_RECORD.class, 0x1E3, State.IN_GAME); // 0x0111 Moreth [H n][n x (D objeto, Q qtd)]
		addPacket(CM_STORYBOOK_APPRAISE.class, 0x196, State.IN_GAME); // 0x00DC Book of Legends, identificação [H n][n x (D objeto, Q qtd)]
		addPacket(CM_STORYBOOK_DISASSEMBLE.class, 0x197, State.IN_GAME); // 0x00DD Book of Legends, desmontagem [H n][n x (D objeto, Q qtd)]
		addPacket(CM_STORYBOOK_REGISTER.class, 0x19E, State.IN_GAME); // 0x00E4 C_USER_STORY_BOOK_REGISTER_ITEM [D livro]
		addPacket(CM_CLIENT_PING_STATE.class, 0x222, State.IN_GAME); // 0x0150 CLIENT_PING_STATE (5.0 Classic)
		addPacket(CM_SHOW_DIALOG.class, 0x00F6, State.IN_GAME); // 0xFFFC USE_OBJECT
		addPacket(CM_CLOSE_DIALOG.class, 0x00F7, State.IN_GAME); // 0xFFFD STOP_USE_OBJECT
		addPacket(CM_CLIENT_SYNC_ACTION.class, 0x00F0, State.IN_GAME, State.AUTHED); // 0x0002 CLIENT_SYNC_ACTION (5.0 Classic)
		addPacket(CM_CLIENT_PING_SYNC.class, 0x0151, State.IN_GAME, State.AUTHED); // 0x00A3 CLIENT_PING_SYNC (5.0 Classic)
		addPacket(CM_SPLIT_ITEM.class, 0x014F, State.IN_GAME); // 0x00B5 SPLIT_ITEM (5.0 Classic: [D origem][Q qtd][C armazem][D destino][C armazem][H slot], 20 b)
		addPacket(CM_CLIENT_SCENE_ACK.class, 0x01A7, State.IN_GAME); // 0x00CD CLIENT_SCENE_ACK (5.0 Classic)
		addPacket(CM_CLIENT_MOTION_ACK.class, 0x0181, State.IN_GAME); // 0x00F3 CLIENT_MOTION_ACK (5.0 Classic)
		addPacket(CM_CLIENT_WORLD_EVENT_ACK.class, 0x01E4, State.IN_GAME); // 0x010E CLIENT_WORLD_EVENT_ACK (5.0 Classic)
		addPacket(CM_CLIENT_STATUS_HEARTBEAT.class, 0x02DF, State.IN_GAME, State.AUTHED); // 0x0225 CLIENT_STATUS_HEARTBEAT (5.0 Classic)

		// Session telemetry & aliases
		addPacket(CM_UI_SETTINGS.class, 0x00E8, State.IN_GAME); // 0x001A SAVE_UI_SETTINGS
		addPacket(CM_UI_SETTINGS.class, 0x001A, State.IN_GAME);
		addPacket(CM_CHAT_AUTH.class, 0x017C, State.IN_GAME); // 0x0086 SIGN_CLIENT
		addPacket(CM_CHAT_AUTH.class, 0x0086, State.IN_GAME);
		addPacket(CM_INSTANCE_INFO.class, 0x01B3, State.IN_GAME); // 0x00C1 INSTANCE_DUNGEON_COOLTIMES
		// sem alias em 0x00C1: esse e o cru do CM_BUY_ITEM (dec 0x0033) e o registro por ultimo apagava a compra e a venda
		addPacket(CM_MAY_QUIT.class, 0x00FE, State.IN_GAME); // 0x0004 READY_TO_QUIT
		addPacket(CM_MAY_QUIT.class, 0x0004, State.IN_GAME);
		addPacket(CM_RECONNECT_AUTH.class, 0x014A, State.AUTHED); // 0x00B8 RECONNECT_AUTH
		addPacket(CM_RECONNECT_AUTH.class, 0x00B8, State.AUTHED);
		addPacket(CM_CLIENT_PERF_METRICS.class, 0x00C5, State.IN_GAME);
		addPacket(CM_CLIENT_PERF_METRICS.class, 0x03DC, State.IN_GAME, State.AUTHED); // 0x0326 client perf/window state telemetry
		addPacket(CM_CLIENT_PERF_METRICS.class, 0x0326, State.IN_GAME, State.AUTHED);
		addPacket(CM_CLIENT_PERF_METRICS.class, 0x03DF, State.IN_GAME, State.AUTHED); // 0x0325 client perf/window state ack
		addPacket(CM_CLIENT_PERF_METRICS.class, 0x0325, State.IN_GAME, State.AUTHED);
		addPacket(CM_PROTOCOL_PING_ACK.class, 0x01D0, State.IN_GAME, State.AUTHED); // 0x0122 PROTOCOL_PING_ACK
		addPacket(CM_PROTOCOL_PING_ACK.class, 0x0122, State.IN_GAME, State.AUTHED);
		addPacket(CM_CLIENT_TELEMETRY_SYNC.class, 0x01E0, State.IN_GAME, State.AUTHED); // 0x0112 CLIENT_TELEMETRY_SYNC (5.0 Classic)
		addPacket(CM_CLIENT_TELEMETRY_SYNC.class, 0x0112, State.IN_GAME, State.AUTHED);

		// ==========================================
		// RANKING 5.0 (Combat Power Ranking 1000..1003)
		// ==========================================
		addPacket(CM_RANKING_INFO.class, 0x01B6, State.IN_GAME); // 0x01B6 WIRE CM_RANKING_INFO (dec=0x00BC)
		addPacket(CM_RANKING_INFO.class, 0x00BC, State.IN_GAME); // Raw alias
		addPacket(CM_RANKING_SUBSCRIBE.class, 0x0181, State.IN_GAME, State.AUTHED); // 0x0181 WIRE CM_RANKING_SUBSCRIBE (dec=0x00F3)
		addPacket(CM_RANKING_SUBSCRIBE.class, 0x00F3, State.IN_GAME, State.AUTHED); // Raw alias
	}

	public AionPacketHandler getPacketHandler() {
		return handler;
	}

	public void addPacket(AionClientPacket prototype) {
		handler.addPacketPrototype(prototype);
	}

	public <T extends AionClientPacket> void addPacket(Class<T> packetClass, int opcode, State state, State... restStates) {
		try {
			Set<State> validStates = EnumSet.of(state, restStates);
			Constructor<T> c;
			try {
				c = packetClass.getConstructor(int.class, State.class, State[].class);
				handler.addPacketPrototype(c.newInstance(opcode, state, restStates));
			} catch (NoSuchMethodException e) {
				c = packetClass.getConstructor(int.class, Set.class);
				handler.addPacketPrototype(c.newInstance(opcode, validStates));
			}
		} catch (Exception e) {
			log.error("Failed to register client packet: " + packetClass.getSimpleName() + " (0x" + Integer.toHexString(opcode) + ")", e);
		}
	}

	@SuppressWarnings("synthetic-access")
	private static class SingletonHolder {
		protected static final AionPacketHandlerFactory instance = new AionPacketHandlerFactory();
	}
}
