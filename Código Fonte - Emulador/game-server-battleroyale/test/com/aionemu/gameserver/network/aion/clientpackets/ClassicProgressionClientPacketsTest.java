package com.aionemu.gameserver.network.aion.clientpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Field;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.Map;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Leitura dos pedidos capturados do Ascend (C 0x106), do Moreth (C 0x111) e do Book of Legends (C 0xDC, 0xDD, 0xE4).
 */
class ClassicProgressionClientPacketsTest {

	@Test
	void ascendRequestFromCapture() throws Exception {
		CM_ITEM_UPGRADE upgrade = read(new CM_ITEM_UPGRADE(0x1FC, EnumSet.of(State.IN_GAME)), "2e040000f32b78c000000000");
		assertEquals(1070, field(upgrade, "recipeId"));
		assertEquals(0xC0782BF3, field(upgrade, "itemObjectId"));
		assertEquals(0, field(upgrade, "optionIndex"));

		// Outros/outros_2026-09-21_14-43-57: Ascend da receita 1071 cancelado com o itemId de origem
		CM_ITEM_UPGRADE_CANCEL cancel = read(new CM_ITEM_UPGRADE_CANCEL(0x230, EnumSet.of(State.IN_GAME)), "5ed95407");
		assertEquals(123001182, field(cancel, "itemId"));
	}

	@Test
	void morosRecordFromCapture() throws Exception {
		CM_MOROS_RECORD record = read(new CM_MOROS_RECORD(0x1E3, EnumSet.of(State.IN_GAME)), "0100fe8340c00100000000000000");
		assertNull(field(record, "invalid"));
		assertEquals(Map.of(0xC04083FE, 1L), field(record, "items"));
	}

	@Test
	void storybookRequestsFromCapture() throws Exception {
		CM_STORYBOOK_APPRAISE appraise = read(new CM_STORYBOOK_APPRAISE(0x196, EnumSet.of(State.IN_GAME)),
			"0400c93441c00b00000000000000c03441c00200000000000000c43441c00200000000000000b73441c00200000000000000");
		assertNull(field(appraise, "invalid"));
		assertEquals(Map.of(0xC04134C9, 11L, 0xC04134C0, 2L, 0xC04134C4, 2L, 0xC04134B7, 2L), field(appraise, "items"));

		CM_STORYBOOK_DISASSEMBLE disassemble = read(new CM_STORYBOOK_DISASSEMBLE(0x197, EnumSet.of(State.IN_GAME)),
			"0500e13741c00100000000000000e43741c00200000000000000ea3741c00100000000000000e23741c00200000000000000e73741c00100000000000000");
		assertNull(field(disassemble, "invalid"));
		assertEquals(5, ((Map<?, ?>) field(disassemble, "items")).size());

		CM_STORYBOOK_REGISTER register = read(new CM_STORYBOOK_REGISTER(0x19E, EnumSet.of(State.IN_GAME)), "06000000");
		assertEquals(6, field(register, "storybookId"));
	}

	@Test
	void itemListRejectsRepeatedObjectAndWrongSize() throws Exception {
		CM_MOROS_RECORD repeated = read(new CM_MOROS_RECORD(0x1E3, EnumSet.of(State.IN_GAME)),
			"0200fe8340c00100000000000000fe8340c00100000000000000");
		assertNotNull(field(repeated, "invalid"));
		CM_MOROS_RECORD shortBody = new CM_MOROS_RECORD(0x1E3, EnumSet.of(State.IN_GAME));
		shortBody.setBuffer(ByteBuffer.wrap(HexFormat.of().parseHex("0200fe8340c00100000000000000")).order(ByteOrder.LITTLE_ENDIAN));
		assertTrue(shortBody.read());
		assertNotNull(field(shortBody, "invalid"));
	}

	private static <T extends AionClientPacket> T read(T packet, String hex) {
		packet.setBuffer(ByteBuffer.wrap(HexFormat.of().parseHex(hex)).order(ByteOrder.LITTLE_ENDIAN));
		assertTrue(packet.read());
		assertEquals(0, packet.getRemainingBytes());
		return packet;
	}

	private static Object field(Object packet, String name) throws Exception {
		for (Class<?> c = packet.getClass(); c != null; c = c.getSuperclass()) {
			try {
				Field f = c.getDeclaredField(name);
				f.setAccessible(true);
				return f.get(packet);
			} catch (NoSuchFieldException e) {
				// campo da superclasse
			}
		}
		throw new NoSuchFieldException(name);
	}
}
