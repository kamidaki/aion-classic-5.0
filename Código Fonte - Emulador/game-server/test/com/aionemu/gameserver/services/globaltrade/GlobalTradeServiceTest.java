package com.aionemu.gameserver.services.globaltrade;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing.State;

/**
 * Ordem e categoria do C_GLOBAL_TRADE_LIST contra as listas capturadas (06_Sistemas_Novos_Global_Auction_House_5.0, categoria 3010000:
 * 25 anúncios da mesma essência).
 */
class GlobalTradeServiceTest {

	private static final long[][] ESSENCES = { { 0x12122aL, 41999999L, 40 }, { 0x1212cbL, 8000000L, 10 }, { 0x121733L, 8000000L, 10 },
		{ 0x121734L, 8000000L, 10 }, { 0x121735L, 8000000L, 10 }, { 0x1225d6L, 28440000L, 36 }, { 0x1229b6L, 79999999L, 100 },
		{ 0x1229bbL, 79999999L, 100 }, { 0x122e6aL, 35000000L, 50 }, { 0x122e6bL, 35000000L, 50 }, { 0x122e6cL, 35000000L, 50 },
		{ 0x122e6fL, 35000000L, 50 }, { 0x122e70L, 35000000L, 50 }, { 0x122f51L, 23000000L, 33 }, { 0x123149L, 69600000L, 100 },
		{ 0x12325cL, 32000000L, 50 }, { 0x12325dL, 32000000L, 50 }, { 0x12365bL, 70000000L, 100 }, { 0x1239b4L, 3500000L, 5 },
		{ 0x123ad5L, 12000000L, 20 }, { 0x123af6L, 20000000L, 41 }, { 0x123cd2L, 16500000L, 30 }, { 0x123cd3L, 16500000L, 30 },
		{ 0x123cd4L, 16500000L, 30 }, { 0x123cd5L, 17000000L, 31 } };

	@Test
	void unitPriceAscendingMatchesCapturedPages() {
		// páginas 0 e 2 da ordem 6 (a página 2 começa no 18º)
		assertEquals(List.of(0x123af6L, 0x123cd5L, 0x123cd2L, 0x123cd3L, 0x123cd4L, 0x123ad5L, 0x12325cL, 0x12325dL, 0x123149L, 0x122f51L, 0x122e6aL,
			0x122e6bL, 0x122e6cL, 0x122e6fL, 0x122e70L, 0x12365bL, 0x1239b4L, 0x1225d6L, 0x1229b6L, 0x1229bbL, 0x1212cbL, 0x121733L, 0x121734L,
			0x121735L, 0x12122aL), sorted(6));
	}

	@Test
	void unitPriceDescendingMatchesCapturedPage() {
		assertEquals(List.of(0x12122aL, 0x121735L, 0x121734L, 0x121733L, 0x1212cbL, 0x1229bbL, 0x1229b6L, 0x1225d6L, 0x1239b4L, 0x12365bL, 0x122e70L,
			0x122e6fL, 0x122e6cL, 0x122e6bL, 0x122e6aL, 0x122f51L, 0x123149L, 0x12325dL), sorted(7).subList(0, 18));
	}

	@Test
	void categoryMatchesByPrefix() {
		assertTrue(GlobalTradeService.inCategory(3010000, 3000000));
		assertTrue(GlobalTradeService.inCategory(3020000, 3000000));
		assertTrue(GlobalTradeService.inCategory(3010000, 3010000));
		assertFalse(GlobalTradeService.inCategory(3020000, 3010000));
		assertTrue(GlobalTradeService.inCategory(1010100, 1010000));
		assertTrue(GlobalTradeService.inCategory(1020101, 1020100));
		assertFalse(GlobalTradeService.inCategory(1020102, 1020101));
		assertFalse(GlobalTradeService.inCategory(1050100, 1040000));
		assertTrue(GlobalTradeService.inCategory(9010000, 2)); // "2" das capturas: a lista inteira
	}

	@Test
	void unitPriceKeepsTwoDecimals() {
		assertEquals(79_999_999, GlobalTradeService.unitPriceX100(79_999_999, 100));
		assertEquals(80_000_000, GlobalTradeService.unitPriceX100(8_000_000, 10));
		assertTrue(GlobalTradeService.compareUnitPrice(99_999_999_999L, 1, 99_999_999_998L, 1) > 0);
		assertEquals(0, GlobalTradeService.compareUnitPrice(3_500_000, 5, 70_000_000, 100));
	}

	private static List<Long> sorted(int sort) {
		List<GlobalTradeListing> listings = new ArrayList<>();
		for (long[] e : ESSENCES)
			listings.add(new GlobalTradeListing(e[0], 1, 2, 166300000, e[2], e[1], GlobalTradeCurrency.KINAH, 3010000, 0, 0, 0, State.LISTED, 0, 0, 0,
				0));
		listings.sort(GlobalTradeService.comparator(sort));
		return listings.stream().map(GlobalTradeListing::getId).toList();
	}
}
