package com.aionemu.gameserver.controllers.attack;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.nio.file.Files;
import java.util.*;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.utils.stats.StatFunctions;

/**
 * Golpes PvP oficiais 5.0 (Gladiador nv60 x Chanter nv61, os dois clientes na mesma captura) passados pela conta do servidor:
 * (ataque + skill − PDef/10) × PVP_DAMAGE_RATIO × (1 + ΔPvP/1000). O ataque do player sorteia entre o mínimo e o máximo da arma, então
 * o teste confere a média da razão oficial/servidor, por grupo (atacante, golpe normal ou skill) e no total.
 */
class PvpDamageReplayTest {

	private static final double TOLERANCIA_TOTAL = 0.03, TOLERANCIA_GRUPO = 0.06;

	@Test
	void officialPvpHitsMatchServerRatio() throws Exception {
		Map<String, List<Double>> grupos = new TreeMap<>();
		List<Double> todos = new ArrayList<>();
		for (String l : Files.readAllLines(new File("test/resources/golpes_oficiais_pvp_50.csv").toPath())) {
			if (l.startsWith("#") || l.startsWith("atacante") || l.isBlank())
				continue;
			String[] c = l.split(";");
			int ataque = Integer.parseInt(c[1]), skill = Integer.parseInt(c[2]), pdef = Integer.parseInt(c[3]), delta = Integer.parseInt(c[4]);
			int dano = Integer.parseInt(c[5]);
			float semPvp = AttackUtil.subtractDefense(ataque + skill, pdef) * (1 + delta / 1000f);
			double razao = dano / (semPvp * StatFunctions.PVP_DAMAGE_RATIO);
			grupos.computeIfAbsent(c[0] + (skill == 0 ? " normal" : " skill"), k -> new ArrayList<>()).add(razao);
			todos.add(razao);
		}
		assertTrue(todos.size() >= 50, "fixture com " + todos.size() + " golpes");
		for (Map.Entry<String, List<Double>> g : grupos.entrySet()) {
			double media = media(g.getValue());
			System.out.printf("%-14s %2d golpes  oficial/servidor %.3f%n", g.getKey(), g.getValue().size(), media);
			assertEquals(1, media, TOLERANCIA_GRUPO, g.getKey());
		}
		double media = media(todos);
		System.out.printf("total %d golpes  oficial/servidor %.3f (com 0,42 seria %.3f)%n", todos.size(), media,
			media * StatFunctions.PVP_DAMAGE_RATIO / 0.42);
		assertEquals(1, media, TOLERANCIA_TOTAL);
	}

	private static double media(List<Double> v) {
		return v.stream().mapToDouble(Double::doubleValue).average().orElse(0);
	}
}
