package com.aionemu.gameserver.dataholders;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.util.List;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.templates.item.ItemUpgradeTemplate;
import com.aionemu.gameserver.model.templates.storybook.StorybookAppraiseTemplate;
import com.aionemu.gameserver.model.templates.storybook.StorybookTemplate;

/**
 * items/item_upgrade.xml, moros/moros.xml e storybook/storybook.xml (gerados por parse_item_upgrade_50.py, parse_moros_50.py e
 * parse_storybook_50.py) contra o que as capturas mostraram.
 */
class ClassicProgressionDataTest {

	@Test
	void ascendRecipes() throws Exception {
		ItemUpgradeData data = (ItemUpgradeData) JAXBContext.newInstance(ItemUpgradeData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/item_upgrade.xml"));
		assertEquals(1318, data.size());

		ItemUpgradeTemplate belt = data.getTemplate(1070); // captura: cinto 123001181 -> 123001182 por 54.150 AP
		assertEquals(123001181, belt.getItemId());
		assertEquals(1, belt.getOptions().size());
		assertEquals(54150, belt.getOption(0).getAp());
		assertEquals(0, belt.getOption(0).getKinah());
		assertEquals(123001182, belt.getOption(0).roll(9999).getItemId());
		assertEquals(ItemUpgradeTemplate.Grade.UP, belt.getOption(0).roll(0).getGrade());
		assertNull(belt.getOption(1));

		ItemUpgradeTemplate sword = data.getTemplate(97); // duas opções: mesmo resultado, material diferente
		assertEquals(2, sword.getOptions().size());
		assertEquals(15, sword.getEnchantMin());
		assertEquals(ItemUpgradeTemplate.Grade.FAIL, sword.getOption(0).roll(8999).getGrade());
		assertEquals(15, sword.getOption(0).roll(8999).getEnchant());
		assertEquals(ItemUpgradeTemplate.Grade.TOP, sword.getOption(1).roll(9999).getGrade());
		assertEquals(1, sword.getOption(1).getMaterials().size());
	}

	@Test
	void morosLevelsAndPoints() throws Exception {
		MorosData data = (MorosData) JAXBContext.newInstance(MorosData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/moros/moros.xml"));
		assertEquals(10, data.getMaxLevel());
		assertEquals(200, data.getLevel(1).getRate());
		assertEquals(8850, data.getLevel(2).getPoints());
		assertEquals(2544, data.getLevel(5).getSkillId());
		assertEquals(3942, data.getLevel(10).getSkillId());
		assertEquals(1, data.getPoint(125002030)); // capacete gravado na captura (gear_etc)
		assertEquals(2, data.getPoint(189720134)); // fragmento (puzzle)
		assertEquals(2, data.getPoint(166000050)); // pedra de encantamento (enchant)
		assertEquals(0, data.getPoint(182400001)); // can_not_record: não pode ser gravado
	}

	@Test
	void storybooksAndAppraise() throws Exception {
		StorybookData data = (StorybookData) JAXBContext.newInstance(StorybookData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/storybook/storybook.xml"));
		assertEquals(16, data.size());
		assertEquals(50, data.appraiseSize());

		StorybookTemplate puzzleF = data.getStorybook(6);
		assertEquals(StorybookTemplate.Type.PUZZLE, puzzleF.getType());
		assertEquals(48, puzzleF.getPieces().size());
		assertEquals(List.of(189720109, 189720110), puzzleF.getPieces().keySet().stream().limit(2).toList());
		assertEquals(2, puzzleF.getModifiers().size()); // critical 5, magicalCritical 1

		StorybookTemplate nature = data.getStorybook(1001);
		assertEquals(30L, nature.getPieces().get(189710000));
		assertEquals(2523, nature.getRewardSkills().getFirst().getSkillId());

		assertEquals(3, data.getStorybook(2001).getRewardItems().size());

		StorybookAppraiseTemplate unknownLegend = data.getAppraise(189720159); // captura: 11 unidades viraram fragmentos F 25 a 32
		for (StorybookAppraiseTemplate.Result result : unknownLegend.getResults())
			assertTrue(puzzleF.getPieces().containsKey(result.getItemId()));
	}
}
