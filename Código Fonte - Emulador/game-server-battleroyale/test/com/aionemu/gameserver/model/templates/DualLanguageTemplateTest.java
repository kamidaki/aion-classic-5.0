package com.aionemu.gameserver.model.templates;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import java.io.StringReader;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.Unmarshaller;
import javax.xml.transform.stream.StreamSource;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.templates.gather.GatherableTemplate;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.itemset.ItemSetTemplate;
import com.aionemu.gameserver.model.templates.npc.NpcTemplate;
import com.aionemu.gameserver.model.templates.pet.PetTemplate;
import com.aionemu.gameserver.model.templates.teleport.TelelocationTemplate;
import com.aionemu.gameserver.model.templates.world.WorldMapTemplate;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;

/**
 * Functional validation test for dual-language entity templates (PT-BR and EN).
 * Ensures getName() returns name_pt and getNameEn() returns name_en.
 */
class DualLanguageTemplateTest {

	private static <T> T unmarshal(String xml, Class<T> clazz) throws Exception {
		JAXBContext ctx = JAXBContext.newInstance(clazz);
		Unmarshaller um = ctx.createUnmarshaller();
		return um.unmarshal(new StreamSource(new StringReader(xml)), clazz).getValue();
	}

	@Test
	@DisplayName("ItemTemplate parses name_pt and name_en and routes getName()/getNameEn() correctly")
	void itemTemplateDualLanguage() throws Exception {
		String xml = "<item_template id=\"100000001\" name_en=\"Circulus's Sword\" name_pt=\"Espada do círculo\" />";
		ItemTemplate item = unmarshal(xml, ItemTemplate.class);

		assertNotNull(item);
		assertEquals("Espada do círculo", item.getName());
		assertEquals("Circulus's Sword", item.getNameEn());
	}

	@Test
	@DisplayName("NpcTemplate parses name_pt and name_en and routes getName()/getNameEn() correctly")
	void npcTemplateDualLanguage() throws Exception {
		String xml = "<npc_template npc_id=\"201000\" name_en=\"Kamikaze Worm\" name_pt=\"Verme Kamikaze\" />";
		NpcTemplate npc = unmarshal(xml, NpcTemplate.class);

		assertNotNull(npc);
		assertEquals("Verme Kamikaze", npc.getName());
		assertEquals("Kamikaze Worm", npc.getNameEn());
	}

	@Test
	@DisplayName("SkillTemplate parses name_pt and name_en and routes getName()/getNameEn() correctly")
	void skillTemplateDualLanguage() throws Exception {
		String xml = "<skill_template skill_id=\"1\" name_en=\"Sword\" name_pt=\"Espada\" />";
		SkillTemplate skill = unmarshal(xml, SkillTemplate.class);

		assertNotNull(skill);
		assertEquals("Espada", skill.getName());
		assertEquals("Sword", skill.getNameEn());
	}

	@Test
	@DisplayName("QuestTemplate parses name_pt and name_en and routes getName()/getNameEn() correctly")
	void questTemplateDualLanguage() throws Exception {
		String xml = "<quest id=\"85\" name_en=\"Symbol of the Chosen\" name_pt=\"Símbolo dos escolhidos\" />";
		QuestTemplate quest = unmarshal(xml, QuestTemplate.class);

		assertNotNull(quest);
		assertEquals("Símbolo dos escolhidos", quest.getName());
		assertEquals("Symbol of the Chosen", quest.getNameEn());
	}

	@Test
	@DisplayName("GatherableTemplate parses name_pt and name_en and routes getName()/getNameEn() correctly")
	void gatherableTemplateDualLanguage() throws Exception {
		String xml = "<gatherable_template id=\"400001\" name_en=\"Kukuru\" name_pt=\"Curto\" />";
		GatherableTemplate gather = unmarshal(xml, GatherableTemplate.class);

		assertNotNull(gather);
		assertEquals("Curto", gather.getName());
		assertEquals("Kukuru", gather.getNameEn());
	}

	@Test
	@DisplayName("PetTemplate parses name_pt and name_en and routes getName()/getNameEn() correctly")
	void petTemplateDualLanguage() throws Exception {
		String xml = "<pet id=\"900000\" name_en=\"Siberian Wild Tiger\" name_pt=\"Tigre selvagem da Sibéria\" />";
		PetTemplate pet = unmarshal(xml, PetTemplate.class);

		assertNotNull(pet);
		assertEquals("Tigre selvagem da Sibéria", pet.getName());
		assertEquals("Siberian Wild Tiger", pet.getNameEn());
	}

	@Test
	@DisplayName("TitleTemplate parses desc_pt, desc_en, name_pt, name_en and routes getters correctly")
	void titleTemplateDualLanguage() throws Exception {
		String xml = "<title_template id=\"1\" desc_en=\"Poeta's Protector\" desc_pt=\"Protetor de poeta\" />";
		TitleTemplate title = unmarshal(xml, TitleTemplate.class);

		assertNotNull(title);
		assertEquals("Protetor de poeta", title.getDesc());
		assertEquals("Poeta's Protector", title.getDescEn());
	}

	@Test
	@DisplayName("WorldMapTemplate and TelelocationTemplate dual-language support")
	void worldMapAndTeleportDualLanguage() throws Exception {
		String mapXml = "<map id=\"110010000\" flags=\"\" name_en=\"Sanctum\" name_pt=\"Santuário\" />";
		WorldMapTemplate map = unmarshal(mapXml, WorldMapTemplate.class);
		assertEquals("Santuário", map.getName());
		assertEquals("Sanctum", map.getNameEn());

		String teleXml = "<teleloc_template id=\"1\" loc_id=\"1\" name_en=\"Sanctum Gate\" name_pt=\"Portão do Santuário\" />";
		TelelocationTemplate tele = unmarshal(teleXml, TelelocationTemplate.class);
		assertEquals("Portão do Santuário", tele.getName());
		assertEquals("Sanctum Gate", tele.getNameEn());
	}

	@Test
	@DisplayName("Fallback behavior when only legacy name or name_en is provided")
	void fallbackBehavior() throws Exception {
		// When only name_pt is present
		String ptXml = "<item_template id=\"1\" name_pt=\"Espada Lendária\" />";
		ItemTemplate itemPtOnly = unmarshal(ptXml, ItemTemplate.class);
		assertEquals("Espada Lendária", itemPtOnly.getName());
		assertEquals("Espada Lendária", itemPtOnly.getNameEn());

		// When only name_en is present
		String enXml = "<item_template id=\"2\" name_en=\"Legendary Sword\" />";
		ItemTemplate itemEnOnly = unmarshal(enXml, ItemTemplate.class);
		assertEquals("Legendary Sword", itemEnOnly.getName());
		assertEquals("Legendary Sword", itemEnOnly.getNameEn());

		// When both are present
		String dualXml = "<item_template id=\"3\" name_en=\"Legendary Sword\" name_pt=\"Espada Lendária\" />";
		ItemTemplate dualItem = unmarshal(dualXml, ItemTemplate.class);
		assertEquals("Espada Lendária", dualItem.getName());
		assertEquals("Legendary Sword", dualItem.getNameEn());

		// Legacy fallback when only name is present
		String legacyXml = "<item_template id=\"4\" name=\"Legacy Sword\" />";
		ItemTemplate legacyItem = unmarshal(legacyXml, ItemTemplate.class);
		assertEquals("Legacy Sword", legacyItem.getName());
		assertEquals("Legacy Sword", legacyItem.getNameEn());
	}
}
