package com.aionemu.gameserver.network.aion;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.serverpackets.SM_USE_OBJECT;
import com.aionemu.gameserver.network.aion.serverpackets.S_CREATE_ACHIEVEMENT_EVENT;
import com.aionemu.gameserver.network.aion.serverpackets.S_BATTLEPASS_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.S_BATTLEPASS_UPDATED;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CREATURE_STATE_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RECOMMENDED_PLAYERS_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_PLAYER_OBJECT_ID_ECHO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ENCHANT_SYNERGY;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COMBAT_BURST_REMOVE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_HUNT_OBJECTIVE_PROGRESS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_TUTORIAL_GUIDE_STATE;
import com.aionemu.gameserver.network.aion.serverpackets.S_CLEAR_ACHIEVEMENT_EVENT;
import com.aionemu.gameserver.network.aion.serverpackets.S_PROGRESS_ACHIEVEMENT;
import com.aionemu.gameserver.network.aion.serverpackets.S_REWARD_ACHIEVEMENT_EVENT_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SPECIAL_SHOP_ITEM_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_AUTO_GROUP_STATUS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ZONE_HAZARD_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_EQUIPMENT_VIEW_STATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COMBAT_BURST_EFFECT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SPECIAL_CURRENCY_SLOTS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DEFAULT_EMOTION_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CUBE_TAB_EXPANSION_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_HOUSING_NOTICE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_NETWORK_SYNC_ACK;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_TERRITORY_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CAMERA_VIEW_MODE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_TERRAIN_SECTOR_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RENDER_GRAPHIC_INIT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_AVATAR_PRESENCE_INIT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_AVATAR_PRESENCE_SYNC;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COSMETIC_TITLE_INIT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_ANVIL_POINTS_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MAP_ZONE_BOUNDS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_BIND_POINT_TELEPORT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CHANNEL_CHATTING_PERMISSION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MAILBOX_INITIAL_STATUS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_REGION_CHAT_CHANNEL_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_TUTORIAL_LOAD_COMPLETED;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CHALLENGE_GUIDE_TABS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ENTER_WORLD_HANDSHAKE_ACK;

public class ServerPacketsOpcodesTest {

	@Test
	public void testServerPacketsOpcodesInitialization() {
		assertDoesNotThrow(() -> {
			Class.forName("com.aionemu.gameserver.network.aion.ServerPacketsOpcodes");
		});
	}

	/** outros2 (22/09): a barra da lápide 701477 da 20541 sai em 0xC4, 13 bytes, começo e fim. */
	@Test
	public void gaugeUsesOfficialOpcode() {
		assertEquals(0xC4, ServerPacketsOpcodes.getOpcode(SM_USE_OBJECT.class));
	}

	@Test
	public void achievementAndBattlepassUseOfficialOpcodes() {
		assertEquals(274, ServerPacketsOpcodes.getOpcode(S_CREATE_ACHIEVEMENT_EVENT.class));
		assertEquals(279, ServerPacketsOpcodes.getOpcode(S_BATTLEPASS_LIST.class));
		assertEquals(280, ServerPacketsOpcodes.getOpcode(S_BATTLEPASS_UPDATED.class));
	}

	@Test
	public void highPriorityRefactoredPacketsUseOfficialOpcodes() {
		assertEquals(197, ServerPacketsOpcodes.getOpcode(SM_CREATURE_STATE_UPDATE.class));
		assertEquals(297, ServerPacketsOpcodes.getOpcode(SM_RECOMMENDED_PLAYERS_LIST.class));
		assertEquals(326, ServerPacketsOpcodes.getOpcode(SM_PLAYER_OBJECT_ID_ECHO.class));
		assertEquals(371, ServerPacketsOpcodes.getOpcode(SM_ENCHANT_SYNERGY.class));
		assertEquals(386, ServerPacketsOpcodes.getOpcode(SM_COMBAT_BURST_REMOVE.class));
		assertEquals(445, ServerPacketsOpcodes.getOpcode(SM_HUNT_OBJECTIVE_PROGRESS.class));
	}

	@Test
	public void mediumPriorityRefactoredPacketsUseOfficialOpcodes() {
		assertEquals(265, ServerPacketsOpcodes.getOpcode(SM_TUTORIAL_GUIDE_STATE.class));
		// 0x110/0x115/0x116 pela tabela de registro de pacotes do Game.dll 5.0 (S_PROGRESS_ACHIEVEMENT, S_REWARD_ACHIEVEMENT_EVENT_RESULT,
		// S_CLEAR_ACHIEVEMENT_EVENT); o 0x110 estava catalogado como SM_ACHIEVEMENT_SEASON_EVENT_INFO
		assertEquals(272, ServerPacketsOpcodes.getOpcode(S_PROGRESS_ACHIEVEMENT.class));
		assertEquals(277, ServerPacketsOpcodes.getOpcode(S_REWARD_ACHIEVEMENT_EVENT_RESULT.class));
		assertEquals(278, ServerPacketsOpcodes.getOpcode(S_CLEAR_ACHIEVEMENT_EVENT.class));
		assertEquals(275, ServerPacketsOpcodes.getOpcode(SM_SPECIAL_SHOP_ITEM_LIST.class));
		assertEquals(309, ServerPacketsOpcodes.getOpcode(SM_AUTO_GROUP_STATUS.class));
		assertEquals(368, ServerPacketsOpcodes.getOpcode(SM_ZONE_HAZARD_LIST.class));
		assertEquals(375, ServerPacketsOpcodes.getOpcode(SM_EQUIPMENT_VIEW_STATE.class));
		assertEquals(385, ServerPacketsOpcodes.getOpcode(SM_COMBAT_BURST_EFFECT.class));
	}

	@Test
	public void lowPriorityAndSyncRefactoredPacketsUseOfficialOpcodes() {
		assertEquals(95, ServerPacketsOpcodes.getOpcode(SM_SPECIAL_CURRENCY_SLOTS.class));
		assertEquals(188, ServerPacketsOpcodes.getOpcode(SM_DEFAULT_EMOTION_LIST.class));
		assertEquals(295, ServerPacketsOpcodes.getOpcode(SM_CUBE_TAB_EXPANSION_INFO.class));
		assertEquals(314, ServerPacketsOpcodes.getOpcode(SM_LEGION_HOUSING_NOTICE.class));
		assertEquals(330, ServerPacketsOpcodes.getOpcode(SM_NETWORK_SYNC_ACK.class));
		assertEquals(350, ServerPacketsOpcodes.getOpcode(SM_LEGION_TERRITORY_INFO.class));
		assertEquals(387, ServerPacketsOpcodes.getOpcode(SM_CAMERA_VIEW_MODE.class));
		assertEquals(396, ServerPacketsOpcodes.getOpcode(SM_TERRAIN_SECTOR_INFO.class));
		assertEquals(401, ServerPacketsOpcodes.getOpcode(SM_RENDER_GRAPHIC_INIT.class));
		assertEquals(407, ServerPacketsOpcodes.getOpcode(SM_AVATAR_PRESENCE_INIT.class));
		assertEquals(424, ServerPacketsOpcodes.getOpcode(SM_AVATAR_PRESENCE_SYNC.class));
		assertEquals(426, ServerPacketsOpcodes.getOpcode(SM_COSMETIC_TITLE_INIT.class));
		assertEquals(427, ServerPacketsOpcodes.getOpcode(SM_SIEL_ANVIL_POINTS_INFO.class));
		assertEquals(428, ServerPacketsOpcodes.getOpcode(SM_MAP_ZONE_BOUNDS.class));
		// 0x128 e 0x1AF pela tabela do Game.dll: S_CHANNEL_CHATTING_PERMISSION e S_HOTSPOT (o 0x1AF estava catalogado como SM_RADAR_INITIAL_STATE)
		assertEquals(296, ServerPacketsOpcodes.getOpcode(SM_CHANNEL_CHATTING_PERMISSION.class));
		assertEquals(431, ServerPacketsOpcodes.getOpcode(SM_BIND_POINT_TELEPORT.class));
		assertEquals(435, ServerPacketsOpcodes.getOpcode(SM_MAILBOX_INITIAL_STATUS.class));
		assertEquals(442, ServerPacketsOpcodes.getOpcode(SM_REGION_CHAT_CHANNEL_INFO.class));
		assertEquals(448, ServerPacketsOpcodes.getOpcode(SM_TUTORIAL_LOAD_COMPLETED.class));
		assertEquals(450, ServerPacketsOpcodes.getOpcode(SM_CHALLENGE_GUIDE_TABS.class));
		assertEquals(453, ServerPacketsOpcodes.getOpcode(SM_ENTER_WORLD_HANDSHAKE_ACK.class));
	}
}
