package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing.State;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Global Auction House e Altar of Transcendence contra as capturas oficiais de 2026-09-11 (06_Sistemas_Novos_Global_Auction_House_5.0 e
 * 06_Sistemas_Novo_Global_Auction_House_and_Altar_of_Transcendences_5.0).
 */
class GlobalTradePacketsTest {

	private static final HexFormat HEX = HexFormat.of();
	private static final long DAY = 24L * 60 * 60 * 1000;

	@Test
	void listPacketMatchesOfficialCapture() throws Exception {
		// último pacote da página 1 (ordem 6) da categoria 3010000: 25 anúncios, 1 entrada; o detalhe só traz a skin
		GlobalTradeListing essence = listing(0x12122A, 166300000, 40, 41_999_999, State.LISTED);
		byte[] body = body(new SM_GLOBAL_TRADE_LIST(25, false, 1, 3010000, false, true, new byte[] { 1, 0, 0, 0 },
			List.of(new SM_GLOBAL_TRADE_LIST.Entry(essence, 18_456_540))));
		assertEquals(499, body.length);
		String officialPrefix = "19000000000100d0ed2d0001000001010000002a121200000000006089e9097fde800200000000dc9f190100000000280000000000000000006089e909";
		assertEquals(officialPrefix, HEX.formatHex(body, 0, officialPrefix.length() / 2));
		for (int i = officialPrefix.length() / 2; i < body.length; i++)
			assertEquals(0, body[i], "byte " + i);
	}

	@Test
	void emptySearchResultMatchesOfficialCapture() throws Exception {
		// Tiamaranta: categoria 1050000 sem anúncio
		assertEquals("00000000000000900510000000010100000000",
			HEX.formatHex(body(new SM_GLOBAL_TRADE_LIST(0, false, 0, 1050000, true, true, new byte[4], List.of()))));
	}

	@Test
	void smallPacketsMatchOfficialCapture() throws Exception {
		assertEquals("0000000000ca9a3b00000000", HEX.formatHex(body(new SM_GLOBAL_TRADE_STATE(1_000_000_000))));
		assertEquals("00b4391200000000000500000000000000", HEX.formatHex(body(new SM_GLOBAL_TRADE_BUY(0x1239B4, 5))));
		assertEquals("0001000000", HEX.formatHex(body(new SM_GLOBAL_TRADE_COLLECT(1))));
		assertEquals("0101010000000000", HEX.formatHex(body(new SM_GLOBAL_TRADE_MYLIST(GlobalTradeCurrency.KINAH, List.of()))));
		assertEquals("0101000000000000", HEX.formatHex(body(new SM_GLOBAL_TRADE_MYLIST(GlobalTradeCurrency.LUNA, List.of()))));
		assertEquals("ae0140c00000000000000000400d03000000000000c2eb0b0000000001000000",
			HEX.formatHex(body(new SM_GLOBAL_TRADE_AVG_PRICE(0xC04001AE, 200_000, 200_000_000, GlobalTradeCurrency.KINAH))));
	}

	@Test
	void salesLogNoticesAndEmptyAnswersMatchOfficialCapture() throws Exception {
		// login da captura do Altar: aviso da Luna vazio, aviso do kinah com a venda de 200.000 (bruto)
		assertEquals("0000000000000000000000000000010101000000000000",
			HEX.formatHex(body(new SM_GLOBAL_TRADE_SALESLOG(GlobalTradeCurrency.LUNA, true, 0, 0, List.of()))));
		assertEquals("400d030000000000000000000000010101010000000000",
			HEX.formatHex(body(new SM_GLOBAL_TRADE_SALESLOG(GlobalTradeCurrency.KINAH, true, 200_000, 0, List.of()))));
		assertEquals("0000000000000000000000000000000101000000000000",
			HEX.formatHex(body(new SM_GLOBAL_TRADE_SALESLOG(GlobalTradeCurrency.LUNA, false, 0, 0, List.of()))));
		assertEquals("0000000000000000000000000000000101010000000000",
			HEX.formatHex(body(new SM_GLOBAL_TRADE_SALESLOG(GlobalTradeCurrency.KINAH, false, 0, 0, List.of()))));
	}

	@Test
	void revenueEntryMatchesOfficialCapture() throws Exception {
		// pedra de ressurreição vendida por 200.000 às 21:29 UTC: 8% de taxa, 184.000 a receber
		GlobalTradeListing sold = new GlobalTradeListing(0x123D1A, 1, 2, 164000010, 1, 200_000, GlobalTradeCurrency.KINAH, 6020000, 2420, 0, 0,
			State.SOLD, 3, 0x01C701E9L * 60_000, 16_000, 0);
		String official = "c0ce0200000000000100000000000001010100000001000a71c609400d0300000000000100000000000000e901c701803e000000000000";
		for (AionServerPacket packet : List.of(new SM_GLOBAL_TRADE_SALESLOG(GlobalTradeCurrency.KINAH, false, 184_000, 1, List.of(sold)),
			new SM_GLOBAL_TRADE_HISTORY(GlobalTradeCurrency.KINAH, 184_000, 1, List.of(sold)))) {
			byte[] body = body(packet);
			assertEquals(499, body.length);
			assertEquals(official, HEX.formatHex(body, 0, official.length() / 2)); // o detalhe do item vendido é lixo de memória no oficial
		}
	}

	@Test
	void commitKeepsOfficialLayout() throws Exception {
		// acabou de ser registrado: 8 dias restantes
		GlobalTradeListing listing = new GlobalTradeListing(0x123D1A, 1, 2, 164000010, 1, 200_000, GlobalTradeCurrency.KINAH, 0, 0, 0,
			System.currentTimeMillis() + 8 * DAY, State.LISTED, 0, 0, 0, 0);
		byte[] body = body(new SM_GLOBAL_TRADE_COMMIT(listing));
		assertEquals(478, body.length);
		assertEquals("001a3d1200000000000a71c609400d030000000000010000000000000008", HEX.formatHex(body, 0, 30));
		assertEquals("00000001000000", HEX.formatHex(body, 471, 478));
	}

	@Test
	void myListAndCancelMatchOfficialCapture() throws Exception {
		// captura de 2026-09-21: pedra de encantamento L50 anunciada por 10 Luna, minutos depois (7 dias restantes), e o cancelamento dela
		GlobalTradeListing luna = new GlobalTradeListing(0x127E0E, 1, 2, 166000050, 1, 10, GlobalTradeCurrency.LUNA, 3010000, 6050, 0,
			System.currentTimeMillis() + 8 * DAY - 15 * 60_000, State.LISTED, 0, 0, 0, 0);
		byte[] body = body(new SM_GLOBAL_TRADE_MYLIST(GlobalTradeCurrency.LUNA, List.of(luna)));
		assertEquals(481, body.length);
		String official = "01010000000001000e7e120000000000b2f5e4090a000000000000000100000000000000070000b2f5e409";
		assertEquals(official, HEX.formatHex(body, 0, official.length() / 2));
		assertEquals("000e7e120000000000", HEX.formatHex(body(new SM_GLOBAL_TRADE_CANCEL(0x127E0E))));

		// o registro do MYLIST é o do COMMIT sem o byte de resultado e sem a moeda final
		byte[] commit = body(new SM_GLOBAL_TRADE_COMMIT(luna));
		assertArrayEquals(Arrays.copyOfRange(commit, 1, 474), Arrays.copyOfRange(body, 8, body.length));
	}

	@Test
	void composePacketsMatchOfficialCapture() throws Exception {
		assertEquals("1000000001e8030000", HEX.formatHex(body(new SM_ITEM_COMPOSE_EVENT(16, SM_ITEM_COMPOSE_EVENT.STARTED, 1000))));
		assertEquals("10000000010001000d8b350b0100000000000000",
			HEX.formatHex(body(new SM_ITEM_COMPOSE_RESULT(16, 1, 1, List.of(new SM_ITEM_COMPOSE_RESULT.Reward(188058381, 1))))));
		assertEquals("05000000010001005f84350b0100000000000000",
			HEX.formatHex(body(new SM_ITEM_COMPOSE_RESULT(5, 1, 1, List.of(new SM_ITEM_COMPOSE_RESULT.Reward(188056671, 1))))));
		assertEquals("10000000020000000c8b350b01000000000000000c8b350b0100000000000000",
			HEX.formatHex(body(new SM_ITEM_COMPOSE_RESULT(16, 2, 0,
				List.of(new SM_ITEM_COMPOSE_RESULT.Reward(188058380, 1), new SM_ITEM_COMPOSE_RESULT.Reward(188058380, 1))))));
	}

	private static GlobalTradeListing listing(long id, int itemId, long count, long price, State state) {
		return new GlobalTradeListing(id, 1, 2, itemId, count, price, GlobalTradeCurrency.KINAH, 0, 0, 0, 0, state, 0, 0, 0, 0);
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
