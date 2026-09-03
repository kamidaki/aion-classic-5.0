package com.aionemu.gameserver.network.factories;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.AionPacketHandler;
import com.aionemu.gameserver.network.aion.clientpackets.*;

public class AionPacketHandlerFactory {
    private AionPacketHandler handler;

    public static AionPacketHandlerFactory getInstance() {
        return SingletonHolder.instance;
    }

    public AionPacketHandlerFactory() {
        handler = new AionPacketHandler();

        // ==========================================
        // CONNECTED / AUTH HANDSHAKE (5.0 Classic)
        // ==========================================
        addPacket(new CM_VERSION_CHECK(0xF2, State.CONNECTED)); // 0x0000 VERSION
        addPacket(new CM_TIME_CHECK(0xE0, State.CONNECTED, State.AUTHED, State.IN_GAME)); // 0x0012 SYNC_TIME
        addPacket(new CM_L2AUTH_LOGIN_CHECK(0x182, State.CONNECTED)); // 0x00F0 HQ_LOGIN
        addPacket(new CM_L2AUTH_LOGIN_CHECK(0x117, State.CONNECTED)); // 0x005D L2AUTH_LOGIN
        addPacket(new CM_L2AUTH_LOGIN_CHECK(0x11F, State.CONNECTED)); // Legacy fallback
        addPacket(new CM_AUTH_SUCCESS(0x00E2, State.AUTHED)); // 0x00E2 READY_ENTER_WORLD_ACK (AUTHED)
        addPacket(new CM_AUTH_SUCCESS(0x190, State.AUTHED, State.IN_GAME)); // 0x0190
        addPacket(new CM_AUTH_SUCCESS(0x193, State.AUTHED, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_LEGION_SEND_EMBLEM_INFO(0x00E2, State.IN_GAME)); // 0x00E2 (dec=0x0010) C_REQUEST_GUILD_NAME (IN_GAME)
        addPacket(new CM_LEGION_SEND_EMBLEM_INFO(0x10, State.IN_GAME)); // Raw alias
        addPacket(new CM_MAC_ADDRESS(0x1AC, State.CONNECTED, State.AUTHED, State.IN_GAME)); // 0x00D6 MACHINE_INFO
        addPacket(new CM_MAC_ADDRESS(0x174, State.CONNECTED, State.AUTHED, State.IN_GAME)); // Legacy fallback

        // ==========================================
        // CHARACTER SELECTION & LOBBY (5.0 Classic)
        // ==========================================
        addPacket(new CM_CHARACTER_LIST(0x114, State.AUTHED)); // 0x005E SESSION_KEY_ECHO
        addPacket(new CM_CHARACTER_LIST(0x11C, State.AUTHED)); // Legacy fallback
        addPacket(new CM_CREATE_CHARACTER(0x115, State.AUTHED)); // 0x005F CREATE_CHARACTER
        addPacket(new CM_CREATE_CHARACTER(0x11D, State.AUTHED)); // Legacy fallback
        addPacket(new CM_DELETE_CHARACTER(0x1E9, State.AUTHED)); // 0x01E9 WIRE DELETE_CHARACTER (dec=0x011B)
        addPacket(new CM_DELETE_CHARACTER(0x11B, State.AUTHED)); // Fallback alias
        addPacket(new CM_DELETE_CHARACTER(0x68, State.AUTHED)); // Raw alias
        addPacket(new CM_RESTORE_CHARACTER(0x11A, State.AUTHED)); // RESTORE_CHARACTER
        addPacket(new CM_CHARACTER_EDIT(0xED, State.AUTHED)); // 0x0017 CHARACTER_EDIT
        addPacket(new CM_CHECK_NICKNAME(0x143, State.AUTHED)); // 0x00B1 CHECK_NICKNAME
        addPacket(new CM_CHECK_NICKNAME(0xB1, State.AUTHED)); // Raw alias
        addPacket(new CM_MAY_LOGIN_INTO_GAME(0x179, State.AUTHED, State.IN_GAME)); // 0x008B SA_ACCOUNT_ITEM_QUERY
        addPacket(new CM_MAY_LOGIN_INTO_GAME(0x8B, State.AUTHED, State.IN_GAME)); // Raw alias
        addPacket(new CM_ENTER_WORLD(0xEA, State.AUTHED)); // 0x0018 ENTER_WORLD
        addPacket(new CM_ENTER_WORLD(0x18, State.AUTHED)); // Raw alias
        addPacket(new CM_CHARACTER_PASSKEY(0x1A0, State.AUTHED)); // 0x00D2 SECOND_PASSWORD
        addPacket(new CM_CHARACTER_PASSKEY(0xD2, State.AUTHED)); // Raw alias
        addPacket(new CM_MAY_QUIT(0xFE, State.AUTHED, State.IN_GAME)); // 0x0004 READY_TO_QUIT
        addPacket(new CM_MAY_QUIT(0xEE, State.AUTHED, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_MAY_QUIT(0x04, State.AUTHED, State.IN_GAME)); // Raw alias
        addPacket(new CM_QUIT(0xF1, State.AUTHED, State.IN_GAME)); // 0x0003 ASK_QUIT
        // addPacket(new CM_RECONNECT_AUTH(0x14A, State.AUTHED, State.IN_GAME)); //
        // 0x00B8 RECONNECT_AUTH
        addPacket(new CM_SHOW_BLOCKLIST(0x14A, State.IN_GAME)); // 0x00B8 SHOW_BLOCKLIST
        addPacket(new CM_RECONNECT_AUTH(0x17A, State.AUTHED, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_PING(0xC6, State.AUTHED, State.IN_GAME)); // 0x002C ALIVE / PING
        addPacket(new CM_PING(0x22B, State.AUTHED, State.IN_GAME)); // 0x0159 PING_159

        // ==========================================
        // IN-GAME WORLD & GAMEPLAY (5.0 Classic)
        // ==========================================
        addPacket(new CM_LEVEL_READY(0xEB, State.AUTHED, State.IN_GAME));  // 0x0019 C_LEVEL_READY (5.0 Classic)
        addPacket(new CM_LEVEL_READY(0x19, State.AUTHED, State.IN_GAME));  // Alias dec opcode
        addPacket(new CM_LEVEL_READY(0x09, State.AUTHED, State.IN_GAME));  // Alias 4.8 opcode
        addPacket(new CM_UI_SETTINGS(0xE8, State.IN_GAME)); // 0x001A UI_SETTINGS
        addPacket(new CM_CHAT_MESSAGE_PUBLIC(0xE9, State.IN_GAME)); // 0x001B CHAT_MESSAGE_PUBLIC
        addPacket(new CM_CHAT_MESSAGE_PUBLIC(0x99, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_CHAT_MESSAGE_WHISPER(0xD6, State.IN_GAME)); // 0x001C CHAT_MESSAGE_WHISPER
        addPacket(new CM_CHAT_MESSAGE_WHISPER(0x96, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_ATTACK(0xD2, State.IN_GAME)); // 0x0020 ATTACK
        addPacket(new CM_CASTSPELL(0xD3, State.IN_GAME)); // 0x0021 USE_SKILL
        addPacket(new CM_TOGGLE_SKILL_DEACTIVATE(0xD0, State.IN_GAME)); // 0x0022 TOGGLE_SKILL
        addPacket(new CM_REMOVE_ALTERED_STATE(0xD1, State.IN_GAME)); // 0x0027 REMOVE_BUFF
        addPacket(new CM_USE_ITEM(0xC7, State.IN_GAME)); // 0x002D USE_ITEM
        addPacket(new CM_USE_ITEM(0xCF, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_EQUIP_ITEM(0xC4, State.IN_GAME)); // 0x002E USE_EQUIPMENT_ITEM
        addPacket(new CM_EQUIP_ITEM(0xCC, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_MOVE(0xC2, State.IN_GAME)); // 0x0030 MOVE_NEW
        addPacket(new CM_MOVE_IN_AIR(0xC3, State.IN_GAME)); // 0x0031 PATH_FLY
        addPacket(new CM_QUESTION_RESPONSE(0xC0, State.IN_GAME)); // 0x0032 QUESTION_RESPONSE
        addPacket(new CM_BUY_ITEM(0xC1, State.IN_GAME)); // 0x0033 BUY_SELL
        addPacket(new CM_SHOW_DIALOG(0xCE, State.IN_GAME)); // 0x0034 SHOW_DIALOG
        addPacket(new CM_TARGET_SELECT(0xCD, State.IN_GAME)); // 0x0037 CHANGE_TARGET
        addPacket(new CM_TARGET_SELECT(0x95, State.IN_GAME)); // Legacy fallback
        addPacket(new CM_PLAYER_LISTENER(0xCA, State.IN_GAME)); // 0x0038 MOVE_OBJECT
        addPacket(new CM_GM_COMMAND_SEND(0xC8, State.IN_GAME)); // 0x003A GM_COMMAND
        addPacket(new CM_EMOTION(0xC9, State.IN_GAME)); // 0x003B EMOTION
        addPacket(new CM_BROKER_SEARCH(0x136, State.IN_GAME)); // 0x003C BROKER_SEARCH
        addPacket(new CM_BROKER_REGISTERED_LIST(0x137, State.IN_GAME)); // 0x003D BROKER_REGISTERED_LIST
        addPacket(new CM_BUY_BROKER_ITEM(0x134, State.IN_GAME)); // 0x003E BUY_BROKER_ITEM
        addPacket(new CM_REGISTER_BROKER_ITEM(0x135, State.IN_GAME)); // 0x003F REGISTER_BROKER_ITEM
        addPacket(new CM_EXCHANGE_ADD_ITEM(0x132, State.IN_GAME)); // 0x0040 EXCHANGE_ADD_ITEM
        addPacket(new CM_EXCHANGE_ADD_KINAH(0x130, State.IN_GAME)); // 0x0042 EXCHANGE_ADD_KINAH
        addPacket(new CM_EXCHANGE_LOCK(0x131, State.IN_GAME)); // 0x0043 EXCHANGE_LOCK
        addPacket(new CM_EXCHANGE_CANCEL(0x12F, State.IN_GAME)); // 0x0055 EXCHANGE_CANCEL
        addPacket(new CM_EXCHANGE_OK(0x12E, State.IN_GAME)); // 0x0054 EXCHANGE_OK
        addPacket(new CM_EXCHANGE_REQUEST(0xF5, State.IN_GAME)); // EXCHANGE_REQUEST
        addPacket(new CM_INIT_LEVEL(0x12C, State.IN_GAME)); // 0x0056 INIT_LEVEL
        addPacket(new CM_PRIVATE_STORE(0x13D, State.IN_GAME)); // 0x0047 PRIVATE_STORE
        addPacket(new CM_PRIVATE_STORE_NAME(0x13A, State.IN_GAME)); // 0x0048 PRIVATE_STORE_NAME
        addPacket(new CM_SUMMON_COMMAND(0x13B, State.IN_GAME)); // 0x0049 SUMMON_COMMAND
        addPacket(new CM_BROKER_LIST(0x139, State.IN_GAME)); // 0x004B BROKER_LIST
        addPacket(new CM_GUILD_WH_KINAH(0x126, State.IN_GAME)); // 0x004C GUILD_WH_KINAH
        addPacket(new CM_PLAY_MOVIE_END(0x123, State.IN_GAME)); // 0x0051 PLAY_MOVIE_END
        addPacket(new CM_GROUP_PLAYER_STATUS_INFO(0x112, State.IN_GAME)); // 0x0060 PARTY
        addPacket(new CM_TEAM_INVITE(0x113, State.IN_GAME)); // 0x0061 PARTY_BY_NAME
        addPacket(new CM_START_LOOT(0x118, State.IN_GAME)); // 0x006A LOOT
        addPacket(new CM_LOOT_ITEM(0x119, State.IN_GAME)); // 0x006B LOOT_ITEM
        addPacket(new CM_GROUP_DISTRIBUTION(0x106, State.IN_GAME)); // 0x006C GROUP_DISTRIBUTION
        addPacket(new CM_SHOW_FRIENDLIST(0x104, State.IN_GAME)); // 0x006E QUERY_BUDDY
        addPacket(new CM_FRIEND_ADD(0x105, State.IN_GAME)); // 0x006F ADD_BUDDY
        addPacket(new CM_FRIEND_DEL(0x102, State.IN_GAME)); // 0x0070 FRIEND_DEL
        addPacket(new CM_DUEL_REQUEST(0x100, State.IN_GAME)); // 0x0072 DUEL_REQUEST
        addPacket(new CM_VIEW_PLAYER_DETAILS(0x10E, State.IN_GAME)); // 0x0074 VIEW_PLAYER_DETAILS
        addPacket(new CM_GG(0x10A, State.IN_GAME)); // 0x0078 GG
        addPacket(new CM_CLIENT_COMMAND_ROLL(0x109, State.IN_GAME)); // 0x007B ROLL
        addPacket(new CM_BROKER_CANCEL_REGISTERED(0x172, State.IN_GAME)); // 0x0080 BROKER_CANCEL
        addPacket(new CM_BROKER_SOLD_LIST(0x173, State.IN_GAME)); // 0x0081 BROKER_SOLD_LIST
        addPacket(new CM_BROKER_COLLECT_SOLD_ITEMS(0x170, State.IN_GAME)); // 0x0082 BROKER_COLLECT
        addPacket(new CM_SHOW_BRAND(0x17F, State.IN_GAME)); // 0x0085 SHOW_BRAND
        addPacket(new CM_CHAT_AUTH(0x17C, State.IN_GAME)); // 0x0086 SIGN_CLIENT
        addPacket(new CM_GROUP_LOOT(0x17B, State.IN_GAME)); // 0x0089 GROUP_LOOT
        addPacket(new CM_DISTRIBUTION_SETTINGS(0x178, State.IN_GAME)); // 0x008A DISTRIBUTION_SETTINGS
        addPacket(new CM_CRAFT(0x167, State.IN_GAME)); // 0x008D CRAFT
        addPacket(new CM_SEND_MAIL(0x16E, State.IN_GAME)); // 0x0094 SEND_MAIL
        addPacket(new CM_CHECK_MAIL_SIZE(0x16F, State.IN_GAME)); // 0x0095 CHECK_MAIL_SIZE
        addPacket(new CM_READ_MAIL(0x16C, State.IN_GAME)); // 0x0096 READ_MAIL
        addPacket(new CM_GET_MAIL_ATTACHMENT(0x16A, State.IN_GAME)); // 0x0098 GET_MAIL_ATTACHMENT
        addPacket(new CM_DELETE_MAIL(0x16B, State.IN_GAME)); // 0x0099 DELETE_MAIL
        addPacket(new CM_READ_EXPRESS_MAIL(0x150, State.IN_GAME)); // 0x00A2 READ_EXPRESS_MAIL
        addPacket(new CM_SELECT_ITEM(0x15A, State.IN_GAME)); // 0x00A8 QUERY_BLOCK
        addPacket(new CM_BLACKCLOUD_MAIL_OPEN(0x15B, State.IN_GAME)); // 0x00A9 BLACKCLOUD_MAIL_OPEN
        addPacket(new CM_BLACKCLOUD_MAIL(0x15F, State.IN_GAME)); // 0x00A5 BLACKCLOUD_MAIL
        addPacket(new CM_BLACKCLOUD_MAIL_CLAIM(0x15C, State.IN_GAME)); // 0x00A6 BLACKCLOUD_MAIL_CLAIM
        addPacket(new CM_PING_REQUEST(0x158, State.IN_GAME)); // 0x00AA CUR_STATUS
        addPacket(new CM_REPLACE_ITEM(0x140, State.IN_GAME)); // 0x00B2 REPLACE_ITEM
        addPacket(new CM_BLOCK_SET_REASON(0x141, State.IN_GAME)); // 0x00B3 BLOCK_SET_REASON
        addPacket(new CM_QUEST_SHARE(0x14E, State.IN_GAME)); // 0x00B4 QUEST_SHARE
        addPacket(new CM_BLOCK_DEL(0x14D, State.IN_GAME)); // 0x00B7 BLOCK_DEL
        addPacket(new CM_FRIEND_STATUS(0x148, State.IN_GAME)); // 0x00BA FRIEND_STATUS
        addPacket(new CM_INSTANCE_INFO(0x1B3, State.IN_GAME)); // 0x00C1 INSTANCE_DUNGEON_COOLTIMES
        addPacket(new CM_BOARD_BUSINESS(0x1BE, State.IN_GAME)); // 0x00C4 BOARD_BUSINESS
        addPacket(new CM_QUEST_TELEPORT(0x1BF, State.IN_GAME)); // 0x00C5 REQUEST_GUILD_HISTORY / QUEST_TELEPORT
        addPacket(new CM_SUMMON_ATTACK(0x1A6, State.IN_GAME)); // 0x00CC SUMMON_ATTACK
        addPacket(new CM_SUMMON_CASTSPELL(0x1A4, State.IN_GAME)); // 0x00CE SUMMON_CASTSPELL
        addPacket(new CM_SHOW_MAP(0x1AF, State.IN_GAME)); // 0x00D5 SHOW_MAP
        addPacket(new CM_AUTO_GROUP(0x1AB, State.IN_GAME)); // 0x00D9 AUTO_GROUP
        addPacket(new CM_SUMMON_MOVE(0x1A8, State.IN_GAME)); // 0x00DA SUMMON_MOVE
        addPacket(new CM_SUMMON_EMOTION(0x1A9, State.IN_GAME)); // 0x00DB SUMMON_EMOTION
        addPacket(new CM_CUSTOM_SETTINGS(0xE6, State.IN_GAME)); // 0x000C CUSTOM_SETTINGS
        addPacket(new CM_CAPTCHA(0xE4, State.IN_GAME)); // 0x000E CAPTCHA
        addPacket(new CM_SET_NOTE(0xF8, State.IN_GAME)); // 0x000A SAVE_CLIENT_SETTINGS
        addPacket(new CM_DIALOG_SELECT(0xF4, State.IN_GAME)); // 0xFFFE DIALOG_SELECT
        addPacket(new CM_OPEN_STATICDOOR(0x9D, State.IN_GAME)); // 0xFFE7 OPEN_STATICDOOR
        addPacket(new CM_TITLE_SET(0x169, State.IN_GAME)); // 0x009B TITLE_SET
        addPacket(new CM_QUESTIONNAIRE(0x163, State.IN_GAME)); // 0x0091 QUESTIONNAIRE
        addPacket(new CM_MOVE_ITEM(0x116, State.IN_GAME)); // MOVE_ITEM
        addPacket(new CM_SPLIT_ITEM(0x117, State.IN_GAME)); // SPLIT_ITEM
        addPacket(new CM_DELETE_ITEM(0x13E, State.IN_GAME)); // DELETE_ITEM
        addPacket(new CM_DELETE_QUEST(0x122, State.IN_GAME)); // DELETE_QUEST
        addPacket(new CM_REVIVE(0xEF, State.IN_GAME)); // REVIVE
        addPacket(new CM_TELEPORT_SELECT(0x11E, State.IN_GAME)); // TELEPORT_SELECT
        addPacket(new CM_MOTION(0x12D, State.IN_GAME)); // MOTION
        addPacket(new CM_FUSION_WEAPONS(0x1A5, State.IN_GAME)); // FUSION_WEAPONS
        addPacket(new CM_BREAK_WEAPONS(0x1A2, State.IN_GAME)); // BREAK_WEAPONS
        addPacket(new CM_PET(0x9C, State.IN_GAME)); // PET
        addPacket(new CM_PET_EMOTE(0x9E, State.IN_GAME)); // PET_EMOTE
        addPacket(new CM_CUBE_EXPAND(0x1BB, State.IN_GAME)); // CUBE_EXPAND
        addPacket(new CM_ENCHANMENT_STONES(0x128, State.IN_GAME)); // ENCHANMENT_STONES
        addPacket(new CM_GATHER(0xE1, State.IN_GAME)); // GATHER
        addPacket(new CM_MACRO_DELETE(0x142, State.IN_GAME)); // MACRO_DELETE
        addPacket(new CM_MACRO_CREATE(0x145, State.IN_GAME)); // MACRO_CREATE
        addPacket(new CM_ABYSS_RANKING_PLAYERS(0x177, State.IN_GAME)); // ABYSS_RANKING_PLAYERS
        addPacket(new CM_WIND_PATH(0x13C, State.IN_GAME)); // 0x0046 WIND_PATH
        addPacket(new CM_CHARGE_ITEM(0x124, State.IN_GAME)); // CHARGE_ITEM
        addPacket(new CM_GUILD_JOIN_REQUEST(0x1EA, State.IN_GAME)); // GUILD_JOIN_REQUEST
        addPacket(new CM_GUILD_JOIN_CANCEL(0x1EB, State.IN_GAME)); // GUILD_JOIN_CANCEL
        addPacket(new CM_GUILD_SEARCH(0x1ED, State.IN_GAME)); // GUILD_SEARCH
        addPacket(new CM_GUILD_TABS(0xFD, State.IN_GAME)); // GUILD_TABS
        addPacket(new CM_EQUIPMENT_CHANGE(0x182, State.IN_GAME)); // EQUIPMENT_CHANGE
        addPacket(new CM_EQUIPMENT_CHANGE_USE(0x183, State.IN_GAME)); // EQUIPMENT_CHANGE_USE
        addPacket(new CM_USER_CLASSIC_WARDROBE_FAVORITE(0x18A, State.IN_GAME)); // WARDROBE_FAVORITE
        addPacket(new CM_USER_CLASSIC_WARDROBE_APPLY(0x18B, State.IN_GAME)); // WARDROBE_APPLY
        addPacket(new CM_USER_CLASSIC_WARDROBE_REMOVE(0x18C, State.IN_GAME)); // WARDROBE_REMOVE
        addPacket(new CM_USER_CLASSIC_WARDROBE_DYE(0x18D, State.IN_GAME)); // WARDROBE_DYE
        addPacket(new CM_USER_CLASSIC_WARDROBE_EXTEND(0x188, State.IN_GAME)); // WARDROBE_EXTEND
        addPacket(new CM_USER_CLASSIC_WARDROBE_REGISTER(0x18F, State.IN_GAME)); // WARDROBE_REGISTER
        addPacket(new CM_BATTLE_PASS_REWARD(0x156, State.IN_GAME)); // BATTLE_PASS_REWARD
        addPacket(new CM_RECIPE_LIST(0x14C, State.AUTHED, State.IN_GAME)); // 0x00B6 RECIPE_LIST (5.0 Classic)
        addPacket(new CM_RECIPE_LIST(0xB6, State.AUTHED, State.IN_GAME));  // Alias dec opcode
        addPacket(new CM_GLOBAL_TRADE(0x1F3, State.IN_GAME)); // 0x0101 GLOBAL_TRADE_SALESLOG (5.0 Classic)
        addPacket(new CM_CLIENT_PING_STATE(0x222, State.IN_GAME)); // 0x0150 CLIENT_PING_STATE (5.0 Classic)
        addPacket(new CM_CUSTOM_SETTING_ACK(0x00F6, State.IN_GAME)); // 0xFFFC CUSTOM_SETTING_ACK
        addPacket(new CM_CUSTOM_SETTING_ACK(0x00F7, State.IN_GAME)); // 0xFFFD CUSTOM_SETTING_ACK2
        addPacket(new CM_SERVER_PVP_ACK(0x03DC, State.IN_GAME)); // 0x0326 SERVER_PVP_ACK (5.0 Classic)
        addPacket(new CM_CLIENT_SYNC_ACTION(0x00F0, State.IN_GAME, State.AUTHED)); // 0x0002 CLIENT_SYNC_ACTION (5.0 Classic)
        addPacket(new CM_CLIENT_PING_SYNC(0x0151, State.IN_GAME, State.AUTHED)); // 0x00A3 CLIENT_PING_SYNC (5.0 Classic)
        addPacket(new CM_CLIENT_ENV_REPORT(0x014F, State.IN_GAME)); // 0x00B5 CLIENT_ENV_REPORT (5.0 Classic)
        addPacket(new CM_CLIENT_SCENE_ACK(0x01A7, State.IN_GAME)); // 0x00CD CLIENT_SCENE_ACK (5.0 Classic)
        addPacket(new CM_CLIENT_MOTION_ACK(0x0181, State.IN_GAME)); // 0x00F3 CLIENT_MOTION_ACK (5.0 Classic)
        addPacket(new CM_CLIENT_WORLD_EVENT_ACK(0x01E4, State.IN_GAME)); // 0x010E CLIENT_WORLD_EVENT_ACK (5.0 Classic)
        addPacket(new CM_CLIENT_STORYBOOK_REQUEST(0x01D0, State.IN_GAME)); // 0x0122 CLIENT_STORYBOOK_REQUEST (5.0 Classic)
        addPacket(new CM_CLIENT_STATUS_HEARTBEAT(0x02DF, State.IN_GAME)); // 0x0225 CLIENT_STATUS_HEARTBEAT (5.0 Classic)
    }

    public AionPacketHandler getPacketHandler() {
        return handler;
    }

    private void addPacket(AionClientPacket prototype) {
        handler.addPacketPrototype(prototype);
    }

    @SuppressWarnings("synthetic-access")
    private static class SingletonHolder {
        protected static final AionPacketHandlerFactory instance = new AionPacketHandlerFactory();
    }
}