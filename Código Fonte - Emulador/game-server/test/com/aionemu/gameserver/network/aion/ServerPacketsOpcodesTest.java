package com.aionemu.gameserver.network.aion;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.serverpackets.SM_USE_OBJECT;

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
}
