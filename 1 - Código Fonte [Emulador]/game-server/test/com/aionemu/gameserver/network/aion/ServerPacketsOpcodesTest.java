package com.aionemu.gameserver.network.aion;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;

public class ServerPacketsOpcodesTest {

	@Test
	public void testServerPacketsOpcodesInitialization() {
		assertDoesNotThrow(() -> {
			Class.forName("com.aionemu.gameserver.network.aion.ServerPacketsOpcodes");
		});
	}
}
