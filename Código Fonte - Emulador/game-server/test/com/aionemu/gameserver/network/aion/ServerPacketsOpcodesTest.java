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
import com.aionemu.gameserver.network.aion.serverpackets.SM_EQUIP_SLOT_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COMBAT_BURST_REMOVE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_HUNT_OBJECTIVE_PROGRESS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_TUTORIAL_GUIDE_STATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ACHIEVEMENT_SEASON_EVENT_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SPECIAL_SHOP_ITEM_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_AUTO_GROUP_STATUS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ZONE_HAZARD_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_EQUIPMENT_VIEW_STATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COMBAT_BURST_EFFECT;

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
		assertEquals(371, ServerPacketsOpcodes.getOpcode(SM_EQUIP_SLOT_UPDATE.class));
		assertEquals(386, ServerPacketsOpcodes.getOpcode(SM_COMBAT_BURST_REMOVE.class));
		assertEquals(445, ServerPacketsOpcodes.getOpcode(SM_HUNT_OBJECTIVE_PROGRESS.class));
	}

	@Test
	public void mediumPriorityRefactoredPacketsUseOfficialOpcodes() {
		assertEquals(265, ServerPacketsOpcodes.getOpcode(SM_TUTORIAL_GUIDE_STATE.class));
		assertEquals(272, ServerPacketsOpcodes.getOpcode(SM_ACHIEVEMENT_SEASON_EVENT_INFO.class));
		assertEquals(275, ServerPacketsOpcodes.getOpcode(SM_SPECIAL_SHOP_ITEM_LIST.class));
		assertEquals(309, ServerPacketsOpcodes.getOpcode(SM_AUTO_GROUP_STATUS.class));
		assertEquals(368, ServerPacketsOpcodes.getOpcode(SM_ZONE_HAZARD_LIST.class));
		assertEquals(375, ServerPacketsOpcodes.getOpcode(SM_EQUIPMENT_VIEW_STATE.class));
		assertEquals(385, ServerPacketsOpcodes.getOpcode(SM_COMBAT_BURST_EFFECT.class));
	}
}
