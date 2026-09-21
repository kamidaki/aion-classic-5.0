package com.aionemu.gameserver.services.item;

import static com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Map;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.services.item.ItemPacketService.ItemDeleteType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;

/**
 * Trailer [D motivo][C 0] do S_CHANGE_ITEM_DESC (0x1D) contra o levantamento das capturas oficiais 5.0.
 */
class ItemUpdateTypeTest {

	private static final Map<ItemUpdateType, Integer> CAPTURED = Map.ofEntries(Map.entry(STATS_CHANGE, 0x00), Map.entry(INC_ITEM_MERGE, 0x01),
		Map.entry(INC_KINAH_MERGE, 0x05), Map.entry(DEC_ITEM_SPLIT, 0x06), Map.entry(DEC_ITEM_USE, 0x16), Map.entry(DEC_STIGMA_USE, 0x00),
		Map.entry(INC_ITEM_COLLECT, 0x19), Map.entry(DEC_KINAH_BUY, 0x1D), Map.entry(INC_KINAH_SELL, 0x20), Map.entry(DEC_ITEM_BUY, 0x44),
		Map.entry(DEC_KINAH_MANASTONE_CLEAR, 0x4A), Map.entry(DEC_KINAH_FLY, 0x4B), Map.entry(INC_ITEM_DECOMPOSE, 0x50),
		Map.entry(DEC_KINAH_CUBE, 0x5A), Map.entry(INC_NPSHOP_GOODS, 0x7A), Map.entry(DEC_KINAH_SOUL_HEALER, 0xE6),
		Map.entry(DEC_SIEL_ANVIL_MATERIAL, 0x115), Map.entry(DEC_KINAH_ENCHANT, 0x118), Map.entry(DEC_KINAH_GODSTONE_CLEAR, 0x11A),
		Map.entry(INC_MANASTONE_CLEAR, 0x11C));

	@Test
	void reasonIsTheCapturedOneOrZero() {
		for (ItemUpdateType type : ItemUpdateType.values())
			assertEquals(CAPTURED.getOrDefault(type, 0), type.getReason(), type.name());
	}

	@Test
	void newItemDecreasesKeepTheUseDeletion() {
		assertEquals(ItemDeleteType.USE, ItemDeleteType.fromUpdateType(DEC_ITEM_USE));
		assertEquals(ItemDeleteType.USE, ItemDeleteType.fromUpdateType(DEC_ITEM_BUY));
		assertEquals(ItemDeleteType.USE, ItemDeleteType.fromUpdateType(DEC_SIEL_ANVIL_MATERIAL));
	}
}
