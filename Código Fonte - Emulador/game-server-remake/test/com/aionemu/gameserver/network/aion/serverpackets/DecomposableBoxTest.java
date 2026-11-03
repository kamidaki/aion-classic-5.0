package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.HexFormat;
import java.util.List;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.DecomposableItemsData;
import com.aionemu.gameserver.dataholders.ItemData;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.templates.item.DecomposableItemInfo;
import com.aionemu.gameserver.model.templates.item.DecomposableSet;
import com.aionemu.gameserver.model.templates.item.DecomposableSetItem;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.actions.DecomposeAction;

/**
 * Caixas do cliente 5.0 contra o que o oficial mostrou na subida 1-60 (wrap_newc_supply_enchant_04_weapon_a_u2_50, personagem asmodiano).
 */
class DecomposableBoxTest {

	/** S 0x104 oficial (212 bytes) para o objeto 0xC01AF6EA. */
	private static final String OFFICIAL_0104 = "eaf61ac00000000001000000000000000f"
		+ "006ae3f5050100000000000f01" + "018269f7050100000000000f01" + "028df0f8050100000000000f01" + "03ff83fd050100000000000f01"
		+ "04c00aff050100000000000f01" + "057b9e03060100000000000f01" + "06f0b809060100000000000f01" + "0741c60c060100000000000f01"
		+ "088ed30f060100000000000f01" + "09da5811060100000000000f01" + "0a54801a060100000000000f01" + "0b07071c060100000000000f01"
		+ "0cf38d1d060100000000000f01" + "0d7a141f060100000000000f01" + "0ebdc5da060100000000000f01";

	@BeforeAll
	static void load() throws Exception {
		DataManager.ITEM_DATA = (ItemData) JAXBContext.newInstance(ItemData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/item_templates.xml"));
		DataManager.DECOMPOSABLE_ITEMS_DATA = (DecomposableItemsData) JAXBContext.newInstance(DecomposableItemsData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/decomposable_items/decomposable_items.xml"));
	}

	private static boolean hasDecompose(int itemId) {
		ItemTemplate t = DataManager.ITEM_DATA.getItemTemplate(itemId);
		return t.getActions() != null && t.getActions().getItemActions().stream().anyMatch(a -> a instanceof DecomposeAction);
	}

	@Test
	void boxesFromTheCapturesAreUsableWithTheOfficialCastTime() {
		// wrap_newc_supply_enchant_04_weapon, wrap_common_rare_title (1000 ms) e wrap_change_medal_04to03 (1500 ms)
		for (int id : new int[] { 188058639, 188058385, 188054071, 186000001 })
			assertTrue(hasDecompose(id), "sem <decompose>: " + id);
		assertEquals(1000, DataManager.ITEM_DATA.getItemTemplate(188058639).getCastingDelay());
		assertEquals(1000, DataManager.ITEM_DATA.getItemTemplate(188058385).getCastingDelay());
		assertEquals(1500, DataManager.ITEM_DATA.getItemTemplate(188054071).getCastingDelay());
	}

	@Test
	void selectionBoxMatchesTheOfficialWindow() {
		DecomposableItemInfo box = DataManager.DECOMPOSABLE_ITEMS_DATA.getSetDecomposable(188058639);
		assertNotNull(box);
		assertTrue(box.isIsSelectable());
		DecomposableSet dark = box.getSets().stream().filter(s -> s.getRace() == Race.ASMODIANS).findFirst().orElseThrow();
		List<DecomposableSetItem> options = dark.getItems();
		assertEquals(102500103, options.get(0x0b).getItemId()); // o indice 11 que o jogador escolheu: gauntlet_d_a_u2_50a
		assertTrue(options.stream().allMatch(o -> o.getEnchant() == 4)); // newc_boost_04_enchant_set

		SM_FIRST_SHOW_DECOMPOSABLE packet = new SM_FIRST_SHOW_DECOMPOSABLE(0xC01AF6EA,
			options.stream().map(o -> new SM_FIRST_SHOW_DECOMPOSABLE.Option(o.getItemId(), o.getCount())).toList());
		ByteBuffer buf = ByteBuffer.allocate(8192).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buf);
		packet.writeImpl(null);
		byte[] body = new byte[buf.position()];
		buf.flip();
		buf.get(body);
		assertEquals(OFFICIAL_0104, HexFormat.of().formatHex(body));
	}

	private static String body(AionServerPacketWriter w) {
		ByteBuffer buf = ByteBuffer.allocate(64).order(ByteOrder.LITTLE_ENDIAN);
		w.write(buf);
		byte[] b = new byte[buf.position()];
		buf.flip();
		buf.get(b);
		return HexFormat.of().formatHex(b);
	}

	private interface AionServerPacketWriter {
		void write(ByteBuffer buf);
	}

	@Test
	void selectionResultMatchesTheOfficialPackets() {
		// S 0x105 da subida 1-60: sucesso com o objeto da caixa, cancelado com objeto 0
		SM_SECONDARY_SHOW_DECOMPOSABLE ok = new SM_SECONDARY_SHOW_DECOMPOSABLE(0xC01AF6EA, SM_SECONDARY_SHOW_DECOMPOSABLE.OK);
		SM_SECONDARY_SHOW_DECOMPOSABLE canceled = new SM_SECONDARY_SHOW_DECOMPOSABLE(0, SM_SECONDARY_SHOW_DECOMPOSABLE.CANCELED);
		assertEquals("eaf61ac00000000000", body(buf -> { ok.setBuf(buf); ok.writeImpl(null); }));
		assertEquals("000000000000000003", body(buf -> { canceled.setBuf(buf); canceled.writeImpl(null); }));
	}

	@Test
	void randomBoxKeepsTheClientSets() {
		// kaisinel_reward_rank01: tres sets garantidos, titulo com 7% e pedra de proc com 2%
		DecomposableItemInfo box = DataManager.DECOMPOSABLE_ITEMS_DATA.getSetDecomposable(188050702);
		assertNotNull(box);
		assertFalse(box.isIsSelectable());
		assertEquals(List.of(1000, 1000, 1000, 70, 20), box.getSets().stream().map(DecomposableSet::getRate).toList());
		assertEquals(300, box.getSets().get(2).getItems().get(0).getCount());
		assertTrue(hasDecompose(188050702));
	}
}
