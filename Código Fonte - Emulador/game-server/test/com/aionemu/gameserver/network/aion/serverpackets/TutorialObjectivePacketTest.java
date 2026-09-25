package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

class TutorialObjectivePacketTest {

	@Test
	void writesEachOfficialObjectiveAndWireCounter() throws Exception {
		assertEquals("01000b000000021700000000000000150000000000000000", hex(new SM_UNK_01BD(SM_UNK_01BD.NORMAL, 21)));
		assertEquals("01000b000000021600000000000000060000000000000000", hex(new SM_UNK_01BD(SM_UNK_01BD.NAMED, 6)));
		assertEquals("01000b000000021500000000000000040000000000000000", hex(new SM_UNK_01BD(SM_UNK_01BD.BOSS, 4)));
	}

	private static String hex(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(32).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		Method method = Arrays.stream(packet.getClass().getDeclaredMethods()).filter(m -> m.getName().equals("writeImpl")).findFirst().orElseThrow();
		method.setAccessible(true);
		method.invoke(packet, new Object[] { (AionConnection) null });
		return HexFormat.of().formatHex(Arrays.copyOf(buffer.array(), buffer.position()));
	}
}
