package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Ascend, Moreth e Book of Legends contra as capturas oficiais: Outros/outros_2026-09-21_06-10-28 (Ascend), 06_Sistemas_Novos_Moreth_5.0 e
 * 06_Sistemas_Novos_Book_of_Legends5.0 (2026-09-11).
 */
class ClassicProgressionPacketsTest {

	private static final HexFormat HEX = HexFormat.of();
	private static final int PLAYER = 0x2E0F3384;

	@Test
	void ascendPacketsMatchOfficialCapture() throws Exception {
		assertEquals("2e04000001e8030000", HEX.formatHex(body(new SM_ITEM_UPGRADE_EVENT(1070, SM_ITEM_UPGRADE_EVENT.STARTED, 1000))));
		// Outros/outros_2026-09-21_14-43-57: receita 1071 iniciada e interrompida pelo C 0x142, duas vezes
		assertEquals("2f04000001e8030000", HEX.formatHex(body(new SM_ITEM_UPGRADE_EVENT(1071, SM_ITEM_UPGRADE_EVENT.STARTED, 1000))));
		assertEquals("000000000200000000", HEX.formatHex(body(new SM_ITEM_UPGRADE_EVENT(0, SM_ITEM_UPGRADE_EVENT.ABORTED, 0))));
		assertEquals("2e04000001005ed954070100000000000000f82c78c0",
			HEX.formatHex(body(new SM_ITEM_UPGRADE_RESULT(1070, List.of(new SM_ITEM_UPGRADE_RESULT.Result(123001182, 1, 0xC0782CF8))))));
	}

	@Test
	void morosInfoMatchesOfficialCaptures() throws Exception {
		assertEquals("010001050000000000001400", HEX.formatHex(body(new SM_MOROS_INFO(1, 1281, 20)))); // login da captura do Moreth
		assertEquals("010003050000000000001300", HEX.formatHex(body(new SM_MOROS_INFO(1, 1283, 19)))); // depois de gravar o capacete
		assertEquals("0200ae0b0000000000001400", HEX.formatHex(body(new SM_MOROS_INFO(2, 2990, 20)))); // login da captura do Ascend
	}

	@Test
	void storybookLoginPacketsMatchOfficialCapture() throws Exception {
		assertEquals("84330f2e0000", HEX.formatHex(body(new SM_STORYBOOK_FINISHED_LIST(PLAYER))));
		List<SM_STORYBOOK_REGISTERED_LIST.Entry> entries = List.of(189700060, 189700061, 189700077, 189700081, 189700084).stream()
			.map(itemId -> new SM_STORYBOOK_REGISTERED_LIST.Entry(2, itemId, 1)).toList();
		assertEquals("84330f2e050084330f2e02000000dc974e0b0100000084330f2e02000000dd974e0b0100000084330f2e02000000ed974e0b01000000"
			+ "84330f2e02000000f1974e0b0100000084330f2e02000000f4974e0b01000000",
			HEX.formatHex(body(new SM_STORYBOOK_REGISTERED_LIST(PLAYER, entries))));
	}

	@Test
	void storybookUpdateMatchesOfficialCapture() throws Exception {
		assertEquals("84330f2e0100000000020001000000cb974e0b0100000001000000cc974e0b01000000", HEX.formatHex(body(new SM_STORYBOOK_UPDATE(PLAYER, 1,
			List.of(new SM_STORYBOOK_UPDATE.Entry(189700043, 1), new SM_STORYBOOK_UPDATE.Entry(189700044, 1))))));
		List<SM_STORYBOOK_UPDATE.Entry> puzzleF = List.of(189720133, 189720134, 189720135, 189720137, 189720138, 189720140).stream()
			.map(itemId -> new SM_STORYBOOK_UPDATE.Entry(itemId, 1)).toList();
		assertEquals("84330f2e060000000006000600000045e64e0b010000000600000046e64e0b010000000600000047e64e0b0100000006000000"
			+ "49e64e0b01000000060000004ae64e0b01000000060000004ce64e0b01000000", HEX.formatHex(body(new SM_STORYBOOK_UPDATE(PLAYER, 6, puzzleF))));
	}

	@Test
	void storybookItemResultsMatchOfficialCapture() throws Exception {
		List<SM_STORYBOOK_ITEM_RESULT.Result> appraised = List.of(result(189720134, 2), result(189720135, 3), result(189720138, 1),
			result(189720133, 3), result(189720137, 1), result(189720140, 1), result(189700084, 1), result(189700076, 1), result(189700062, 1),
			result(189700061, 1), result(189700044, 1), result(189700043, 1));
		assertEquals("000000000c0046e64e0b020000000000000047e64e0b03000000000000004ae64e0b010000000000000045e64e0b030000000000000049e64e0b0100"
			+ "0000000000004ce64e0b0100000000000000f4974e0b0100000000000000ec974e0b0100000000000000de974e0b0100000000000000dd974e0b0100000000000000"
			+ "cc974e0b0100000000000000cb974e0b0100000000000000", HEX.formatHex(body(new SM_STORYBOOK_APPRAISE_RESULT(appraised))));
		assertEquals("0000000003000a2e360b0500000000000000d92d360b0100000000000000db2d360b0100000000000000", HEX.formatHex(body(
			new SM_STORYBOOK_DISASSEMBLE_RESULT(List.of(result(188100106, 5), result(188100057, 1), result(188100059, 1))))));
	}

	private static SM_STORYBOOK_ITEM_RESULT.Result result(int itemId, long count) {
		return new SM_STORYBOOK_ITEM_RESULT.Result(itemId, count);
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(8192).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		Method method = null;
		for (Class<?> c = packet.getClass(); method == null; c = c.getSuperclass())
			method = Arrays.stream(c.getDeclaredMethods()).filter(m -> m.getName().equals("writeImpl")).findFirst().orElse(null);
		method.setAccessible(true);
		method.invoke(packet, new Object[] { (AionConnection) null });
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
