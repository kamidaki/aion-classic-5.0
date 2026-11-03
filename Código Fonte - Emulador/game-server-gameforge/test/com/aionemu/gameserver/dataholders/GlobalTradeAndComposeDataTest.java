package com.aionemu.gameserver.dataholders;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.templates.item.ItemComposeRecipe;

/**
 * items/global_trade.xml e items/item_compose.xml (gerados por parse_global_trade_50.py e parse_item_compose_50.py) contra os itens das
 * capturas de 2026-09-11.
 */
class GlobalTradeAndComposeDataTest {

	@Test
	void globalTradeItems() throws Exception {
		GlobalTradeData data = (GlobalTradeData) JAXBContext.newInstance(GlobalTradeData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/global_trade.xml"));
		assertEquals(32454, data.size());
		// pedra de ressurreição anunciada em kinah e em Luna na captura
		assertTrue(data.canRegister(164000010, GlobalTradeCurrency.KINAH));
		assertTrue(data.canRegister(164000010, GlobalTradeCurrency.LUNA));
		assertEquals(6020000, data.getCategory(164000010));
		// essência comprada na captura, categoria 3010000
		assertEquals(3010000, data.getCategory(166300000));
		// item world_cash: só Luna
		assertFalse(data.canRegister(110900715, GlobalTradeCurrency.KINAH));
		assertTrue(data.canRegister(110900715, GlobalTradeCurrency.LUNA));
		// rare_title_token (material do Altar) não é anunciável
		assertFalse(data.canRegister(186020497, GlobalTradeCurrency.KINAH));
	}

	@Test
	void composeRecipes() throws Exception {
		ItemComposeData data = (ItemComposeData) JAXBContext.newInstance(ItemComposeData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/item_compose.xml"));
		assertEquals(16, data.size());

		ItemComposeRecipe titles = data.getRecipe(16); // captura: 6 rare_title_token, 220.000 de kinah, resultado UP 188058381
		assertEquals(6, titles.getMaterialCount());
		assertEquals(220_000, titles.getFee());
		assertTrue(titles.isMaterial(186020497));
		assertEquals(ItemComposeRecipe.Grade.SAME, titles.roll(7999).getGrade());
		assertEquals(188058381, titles.roll(8000).getItemId());

		ItemComposeRecipe manastones = data.getRecipe(5); // captura: 6 manastones do grupo 5, 25.000, resultado UP 188056671
		assertEquals(25_000, manastones.getFee());
		assertTrue(manastones.isMaterial(167000267));
		assertEquals(188056671, manastones.roll(2500).getItemId());
		assertEquals(2, manastones.roll(9999).getCount()); // TOP: 2 do mesmo item

		assertEquals(2, data.getRecipe(6).getMaterialCount()); // fusão de godstone fabled: 2 materiais
	}
}
