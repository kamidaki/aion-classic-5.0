package com.aionemu.gameserver.dataholders;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Stream;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.Unmarshaller;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.templates.npcskill.NpcSkillTargetAttribute;
import com.aionemu.gameserver.model.templates.npcskill.NpcSkillTemplate;
import com.aionemu.gameserver.model.templates.npcskill.NpcSkillTemplates;

/**
 * Listas dos guardas de torre de Tiamaranta (fix_50_torre_skills.py): carregam pelo JAXB do servidor, nenhum guarda tem lista
 * em outro arquivo (o NpcSkillData fica só com a primeira) e a cadeia fecha em laço.
 */
class TowerGuardSkillsTest {

	private static final String ARQUIVO = "800040000_Tiamaranta_Mesa.xml";

	@Test
	void towerGuardListsLoadAndLoop() throws Exception {
		Unmarshaller u = JAXBContext.newInstance(NpcSkillData.class).createUnmarshaller();
		Map<Integer, List<String>> onde = new HashMap<>();
		Map<Integer, NpcSkillTemplates> torre = new HashMap<>();
		List<Path> arquivos;
		try (Stream<Path> s = Files.walk(new File("data/static_data/npc_skills").toPath())) {
			arquivos = s.filter(p -> p.toString().endsWith(".xml")).sorted().toList();
		}
		for (Path p : arquivos) {
			NpcSkillData d = (NpcSkillData) u.unmarshal(p.toFile());
			Set<NpcSkillTemplates> listas = Collections.newSetFromMap(new IdentityHashMap<>()); // o mapa repete a lista por npcId
			listas.addAll(d.getAllNpcSkillTemplates());
			for (NpcSkillTemplates t : listas) {
				for (int id : t.getNpcIds()) {
					onde.computeIfAbsent(id, k -> new ArrayList<>()).add(p.getFileName().toString());
					if (p.getFileName().toString().equals(ARQUIVO) && id >= 274000 && id < 275000)
						torre.put(id, t);
				}
			}
		}
		assertEquals(288, torre.size(), "guardas Li/Da/Dr x As/Fi/Pr/Wi com lista");
		for (int id : torre.keySet())
			assertEquals(List.of(ARQUIVO), onde.get(id), "guarda " + id + " com lista em mais de um lugar");

		// Balaur assassino (274191, capturado na 4412): 18166 abre, depois 17332 -> 17326 -> 17689 -> 17332...
		assertLoop(torre.get(274191), new int[] { 18166, 17332, 17326, 17689 }, 1);
		// Elyos guerreiro (274028, capturado) e o Asmodiano da mesma classe (274020): 17081 <-> 17082
		assertLoop(torre.get(274028), new int[] { 17081, 17082, 17081 }, 1);
		assertLoop(torre.get(274020), new int[] { 17081, 17082, 17081 }, 1);
		NpcSkillTemplate cura = torre.get(274193).getNpcSkills().stream().filter(s -> s.getSkillId() == 17365).findFirst().orElseThrow();
		assertEquals(NpcSkillTargetAttribute.FRIEND, cura.getTarget());
	}

	/** Segue a cadeia a partir da abertura (chain_id 0) e confere a ordem e que a última volta para a de chain_id {@code volta}. */
	private static void assertLoop(NpcSkillTemplates lista, int[] ordem, int volta) {
		List<NpcSkillTemplate> s = lista.getNpcSkills();
		NpcSkillTemplate atual = s.stream().filter(e -> e.getChainId() == 0).findFirst().orElseThrow();
		for (int i = 0; i < ordem.length; i++) {
			assertEquals(ordem[i], atual.getSkillId(), "passo " + i);
			assertEquals(100, atual.getProbability());
			assertTrue(atual.getMaxChainTime() > atual.getNextSkillTime());
			int prox = atual.getNextChainId();
			if (i == ordem.length - 1) {
				assertEquals(volta, prox, "fechamento do laço");
				break;
			}
			atual = s.stream().filter(e -> e.getChainId() == prox).findFirst().orElseThrow();
		}
	}
}
