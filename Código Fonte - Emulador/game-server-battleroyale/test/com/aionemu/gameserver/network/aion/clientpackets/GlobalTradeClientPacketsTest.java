package com.aionemu.gameserver.network.aion.clientpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Field;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Leitura dos pedidos do cliente capturados (Altar e busca por nome na Auction House).
 */
class GlobalTradeClientPacketsTest {

	@Test
	void composeRequestsFromCapture() throws Exception {
		CM_ITEM_COMPOSE titles = read(new CM_ITEM_COMPOSE(0x22E, EnumSet.of(State.IN_GAME)), "1000000001009172160b060000000000000001");
		assertNull(field(titles, "invalid"));
		assertEquals(16, field(titles, "recipeId"));
		assertEquals(Map.of(186020497, 6L), field(titles, "materials"));
		assertEquals(1, field(titles, "quantity"));

		CM_ITEM_COMPOSE twoTitles = read(new CM_ITEM_COMPOSE(0x22E, EnumSet.of(State.IN_GAME)),
			"1000000001009172160b060000000000000002");
		assertNull(field(twoTitles, "invalid"));
		assertEquals(Map.of(186020497, 6L), field(twoTitles, "materials"));
		assertEquals(2, field(twoTitles, "quantity"));

		CM_ITEM_COMPOSE manastones = read(new CM_ITEM_COMPOSE(0x22E, EnumSet.of(State.IN_GAME)), "050000000100cb38f409060000000000000001");
		assertNull(field(manastones, "invalid"));
		assertEquals(Map.of(167000267, 6L), field(manastones, "materials"));
	}

	@Test
	void composeRequestWithTwoMaterials() throws Exception {
		// mesmo layout com n = 2 (D quantidade + D 0 + C fusões)
		CM_ITEM_COMPOSE mixed = read(new CM_ITEM_COMPOSE(0x22E, EnumSet.of(State.IN_GAME)),
			"050000000200cb38f40904000000cc38f40902000000" + "0000000001");
		assertNull(field(mixed, "invalid"));
		assertEquals(Map.of(167000267, 4L, 167000268, 2L), field(mixed, "materials"));
	}

	@Test
	void clearTitleRequestUsesTwoNegativeIntsInClassic() throws Exception {
		CM_TITLE_SET clear = read(new CM_TITLE_SET(0x09B, EnumSet.of(State.IN_GAME)), "ffffffffffffffff");
		assertEquals(-1, field(clear, "titleId"));
		assertEquals(-1, field(clear, "bonusTitleId"));
	}

	@Test
	void searchRequestFromCapture() throws Exception {
		// Inshagle: busca por nome na categoria 3020000, 14 itemIds
		CM_GLOBAL_TRADE_LIST search = read(new CM_GLOBAL_TRADE_LIST(0x1EE, EnumSet.of(State.IN_GAME)),
			"070000e0142e00010000000e00ab38f409cb38f409eb38f4090b39f4092b39f4096b39f4098b39f409ab39f409ca39f409e639f409ee39f4090d3af4091b3af409223af409");
		assertTrue((Boolean) field(search, "valid"));
		assertEquals(7, field(search, "sort"));
		assertEquals(0, field(search, "page"));
		assertEquals(3020000, field(search, "category"));
		assertArrayEquals(new byte[] { 1, 0, 0, 0 }, (byte[]) field(search, "tail"));
		assertEquals(14, ((Set<?>) field(search, "itemIds")).size());
		assertTrue(((Set<?>) field(search, "itemIds")).contains(167000558));
	}

	@Test
	void buyRequestWithAndWithoutCount() throws Exception {
		// oficial: só o anúncio (captura de 2026-09-21); com o version.dll, compra dividida com [D quantidade] no fim
		CM_GLOBAL_TRADE_BUY whole = read(new CM_GLOBAL_TRADE_BUY(0x1EC, EnumSet.of(State.IN_GAME)), "f87d120000000000");
		assertEquals(0x127df8L, field(whole, "listingId"));
		assertEquals(0L, field(whole, "count"));
		CM_GLOBAL_TRADE_BUY part = read(new CM_GLOBAL_TRADE_BUY(0x1EC, EnumSet.of(State.IN_GAME)), "f87d12000000000005000000");
		assertEquals(0x127df8L, field(part, "listingId"));
		assertEquals(5L, field(part, "count"));
	}

	private static <T extends AionClientPacket> T read(T packet, String hex) {
		packet.setBuffer(ByteBuffer.wrap(HexFormat.of().parseHex(hex)).order(ByteOrder.LITTLE_ENDIAN));
		assertTrue(packet.read());
		assertEquals(0, packet.getRemainingBytes());
		return packet;
	}

	private static Object field(Object packet, String name) throws Exception {
		Field f = packet.getClass().getDeclaredField(name);
		f.setAccessible(true);
		return f.get(packet);
	}
}
