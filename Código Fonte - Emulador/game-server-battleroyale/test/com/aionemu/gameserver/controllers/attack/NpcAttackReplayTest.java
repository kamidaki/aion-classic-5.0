package com.aionemu.gameserver.controllers.attack;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.nio.file.Files;
import java.util.*;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.NpcData;
import com.aionemu.gameserver.model.stats.calc.NpcStatCalculation;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.model.templates.npc.NpcTemplate;
import com.aionemu.gameserver.utils.stats.StatFunctions;

/**
 * Golpes de mob no personagem das capturas oficiais 5.0 (S_ATTACK 0x36, golpe normal, PDef do S_STATUS) passados pela conta do
 * servidor: ataque do NPC (template ou curva) × 80–120% − PDef/10. Fixture gerada por
 * {@code fix_50_npc_ataque.py --exportar-golpes test/resources/golpes_oficiais_npc_50.csv}.
 * <p>
 * Só entram mobs com amostra limpa, pelos mesmos critérios do script: 8+ golpes, nenhum golpe de 1 (roteirizado), p90/p10 ≤ 1,6 e
 * golpes que cabem num ataque só com 80–120%.
 */
class NpcAttackReplayTest {

	private static final int MIN_GOLPES = 8;
	private static final double MAX_ESPALHAMENTO = 1.6, MIN_DENTRO = 0.9;
	private static final int TOLERANCIA = 2; // arredondamento do dano para inteiro

	@Test
	void officialHitsFallInsideServerRange() throws Exception {
		NpcData npcs = (NpcData) JAXBContext.newInstance(NpcData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/npcs/npc_templates.xml"));

		Map<Integer, List<int[]>> golpes = new TreeMap<>();
		List<String> linhas = Files.readAllLines(new File("test/resources/golpes_oficiais_npc_50.csv").toPath());
		for (String l : linhas.subList(1, linhas.size())) {
			String[] c = l.split(";");
			golpes.computeIfAbsent(Integer.parseInt(c[0]), k -> new ArrayList<>()).add(new int[] { Integer.parseInt(c[1]), Integer.parseInt(c[2]) });
		}

		int limpos = 0, okServidor = 0, okCurva = 0;
		List<String> falhas = new ArrayList<>();
		for (Map.Entry<Integer, List<int[]>> e : golpes.entrySet()) {
			List<int[]> v = e.getValue();
			int[] danos = v.stream().mapToInt(g -> g[0]).sorted().toArray();
			if (v.size() < MIN_GOLPES || danos[0] <= 1 || (double) danos[danos.length * 9 / 10] / danos[danos.length / 10] > MAX_ESPALHAMENTO)
				continue;
			double maxImpl = v.stream().mapToDouble(g -> g[0] + g[1] / 10.0).max().orElseThrow();
			double minImpl = v.stream().mapToDouble(g -> g[0] + g[1] / 10.0).min().orElseThrow();
			if (maxImpl / 1.2 > minImpl / 0.8) // golpes que não cabem em nenhum ataque com 80–120%: fora da medição
				continue;
			NpcTemplate t = npcs.getNpcTemplate(e.getKey());
			assertNotNull(t, "npc " + e.getKey() + " sem template");
			limpos++;
			int atk = t.getStatsTemplate().getAttack();
			int curva = NpcStatCalculation.calculateStat(StatEnum.PHYSICAL_ATTACK, t.getRating(), t.getRank(), t.getLevel());
			double dentro = fracaoDentro(v, atk), dentroCurva = fracaoDentro(v, curva);
			if (dentro >= MIN_DENTRO)
				okServidor++;
			else
				falhas.add(String.format("%d (%s): ataque %d, %.0f%% dos %d golpes dentro", e.getKey(), t.getName(), atk, dentro * 100, v.size()));
			if (dentroCurva >= MIN_DENTRO)
				okCurva++;
			System.out.printf("%7d %-30s ataque %5d (curva %5d)  dentro %3.0f%% (curva %3.0f%%)  %d golpes%n", e.getKey(), t.getName(), atk, curva,
				dentro * 100, dentroCurva * 100, v.size());
		}
		System.out.printf("mobs limpos: %d | reproduzidos pelo servidor: %d | pela curva antiga: %d%n", limpos, okServidor, okCurva);
		assertTrue(limpos > 0, "fixture sem mob limpo");
		assertTrue(falhas.isEmpty(), "golpes oficiais fora da faixa do servidor:\n" + String.join("\n", falhas));
	}

	/** Fração dos golpes oficiais que caem em [ataque×80% − PDef/10, ataque×120% − PDef/10], mínimo 1, como no AttackUtil. */
	private static double fracaoDentro(List<int[]> golpes, int ataque) {
		int dentro = 0;
		for (int[] g : golpes) {
			float lo = Math.max(1, AttackUtil.subtractDefense(StatFunctions.npcAttackRoll(ataque, StatFunctions.NPC_ROLL_MIN), g[1]));
			float hi = Math.max(1, AttackUtil.subtractDefense(StatFunctions.npcAttackRoll(ataque, StatFunctions.NPC_ROLL_MAX), g[1]));
			if (g[0] >= lo - TOLERANCIA && g[0] <= hi + TOLERANCIA)
				dentro++;
		}
		return (double) dentro / golpes.size();
	}
}
