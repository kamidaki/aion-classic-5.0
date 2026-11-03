package com.aionemu.gameserver.model.team.legion;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.LegionGrowthData;

/**
 * Crescimento da Legion pelo legion/legion_growth.xml (client_guild_growth.xml) contra as capturas: Lost Academy com 3000 de exp no nível 1
 * depois da primeira recompensa (S 0x164, 22/09) e Org Asmo no nível 44 com 88500.
 */
class LegionGrowthTest {

	@Test
	void expLevelsUpByClientTable() throws Exception {
		DataManager.LEGION_GROWTH_DATA = (LegionGrowthData) JAXBContext.newInstance(LegionGrowthData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/legion/legion_growth.xml"));
		assertEquals(100, DataManager.LEGION_GROWTH_DATA.getMaxLevel());

		Legion legion = new Legion(1, "Lost Academy");
		assertEquals(0, legion.addGrowthExp(3000));
		assertEquals(1, legion.getGrowthLevel());
		assertEquals(3000, legion.getGrowthExp());

		assertEquals(1, legion.addGrowthExp(27000 + 500)); // o nível 2 pede 30000
		assertEquals(2, legion.getGrowthLevel());
		assertEquals(500, legion.getGrowthExp());

		legion.setGrowth(44, 88500, 0, 0);
		assertEquals(0, legion.addGrowthExp(140000 - 88500 - 1)); // o 45 pede 140000
		assertEquals(1, legion.addGrowthExp(1));
		assertEquals(45, legion.getGrowthLevel());
		assertEquals(0, legion.getGrowthExp());

		legion.setGrowth(100, 0, 0, 0);
		legion.addGrowthExp(5000);
		assertEquals(0, legion.getGrowthExp()); // último nível: a exp não acumula
		legion.addEssence(0, 10);
		assertEquals(10, legion.getEssencePiece());
	}
}
