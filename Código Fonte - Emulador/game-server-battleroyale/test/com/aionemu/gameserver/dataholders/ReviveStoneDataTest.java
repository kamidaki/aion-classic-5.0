package com.aionemu.gameserver.dataholders;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.templates.item.ItemTemplate;

/**
 * Pedras de ressurreição no item_templates.xml (fix_50_item_self_resurrect.py e fix_50_item_activation_skill.py): as de auto-ressurreição
 * têm a marca I_RESURRECT do cliente, e todas usam a skill 9912 item_soulstone_resurrect_01 (captura de 2026-09-21, C_DEAD_RESTART tipo 2).
 */
class ReviveStoneDataTest {

	@Test
	void selfResurrectStonesComeFromClientTag() throws Exception {
		ItemData items = (ItemData) JAXBContext.newInstance(ItemData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/item_templates.xml"));
		for (int itemId : new int[] { 161001003, 188053614, 161001001, 161001004, 161000003, 161000004 }) {
			ItemTemplate stone = items.getItemTemplate(itemId);
			assertTrue(stone.isSelfResurrect(), itemId + " revive o dono");
			assertEquals(9912, stone.getActions().getSkillUseAction().getSkillId(), itemId + " usa item_soulstone_resurrect_01");
		}
		ItemTemplate allyOnly = items.getItemTemplate(164000010); // soulstone_resurrect_other_10: só ressuscita aliado
		assertFalse(allyOnly.isSelfResurrect());
		assertEquals(9912, allyOnly.getActions().getSkillUseAction().getSkillId());
	}
}
