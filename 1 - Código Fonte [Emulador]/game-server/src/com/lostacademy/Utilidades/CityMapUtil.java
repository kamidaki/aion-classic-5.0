package com.lostacademy.Utilidades;

import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Lista de mapas cidades e mapas em que mobs ficam em lugares abertos 
 * (linha direta de visão) ou de teste que não precisam de NAV.
 *
 * @author KAMIDAKI
 */
public final class CityMapUtil {

	private CityMapUtil() {
		throw new AssertionError("Classe utilitária não deve ser instanciada");
	}
	
	// Mapas de cidades principais
	private static final int[] CITY_MAPS = {
		110010000, // Sanctum
		110030000, // sanctum gate
		110020000, // Cloister of Kaisinel
		110070000, // Kaisinel Academy
		120010000, // Pandaemonium
		120020000, // Convent of Marchutan
		120080000, // Marchutan Priory
		130090000, // Wisplight Abbey
		140010000  // Fatebound Abbey
	};

	// Mapas de arena e PvP
	private static final int[] ARENA_MAPS = {
		300300000, // Empyrean Crucible
		300320000, // Crucible Challenge
		300350000, // Arena of Chaos
		300360000, // Arena of Discipline
		300420000, // Chaos Training Grounds
		300430000, // Discipline Training Grounds
		300450000, // Arena of Harmony
		300550000  // Arena of Glory
	};

	// Mapas especiais e de instância
	private static final int[] SPECIAL_MAPS = {
		300030000, // Nochsana Training Camp
		220090000, // Habrok
		210090000, // Idian Depths Light
		220100000, // Idian Depths Dark
		310060000, // Sliver of Darkness
		310070000, // Sliver of Darkness (Stigma)
		320060000, // Space of Oblivion
		320070000, // Space of Destiny
		300460000, // Steel Rake Cabin
		300100000, // Steel Rake
		400020000, // Belus
		400040000, // Aspida
		400050000, // Atanatos
		400060000, // Disillon
		510010000, // LF Prison
		520010000, // DF Prison
		600080000  // Live Party Concert Hall
	};

	// Mapas de Karamatis e Ataxiar
	private static final int[] REGION_MAPS = {
		310010000, // Karamatis1
		310020000, // Karamatis2
		310030000, // Aerdina
		310040000, // Geranaia
		310120000, // Karamatis3
		320010000, // Ataxiar1
		320020000, // Ataxiar2
		320030000, // Bregirun
		320040000, // Nidalber
		320140000  // Ataxiar3
	};

	// Mapas de teste
	private static final int[] TEST_MAPS = {
		300010000, // IDAbPro
		300020000, // IDTest Dungeon
		300290000, // Test MRT IDZone
		900020000, // TestBasic
		900030000, // Test Server
		900100000, // Test Giant Monster
		900110000, // Housing Barrack
		900120000, // Test IDArena
		900130000, // IDLDF5RE test
		900140000, // Instanced Dungeon Test
		900150000, // Instanced Dungeon Test2
		900170000, // test intro
		900180000, // Test server art
		900190000, // Tag Match Test Level
		900200000, // Test TimeAttack Instanced Dungeon 02
		900220000  // System Basic
	};

	private static final Set<Integer> NO_AI_MAPS = initializeNoAiMaps();

	private static Set<Integer> initializeNoAiMaps() {
		return Stream.of(CITY_MAPS, ARENA_MAPS, SPECIAL_MAPS, REGION_MAPS, TEST_MAPS)
			.flatMapToInt(java.util.Arrays::stream)
			.boxed()
			.collect(Collectors.toUnmodifiableSet());
	}

	/**
	 * Verifica se o mapa deve usar somente pathfinding padrão.
	 *
	 * @param mapId ID do mapa a verificar
	 * @return true se o mapa não precisa de NavMesh
	 */
	public static boolean isDefaultPathfinding(int mapId) {
		return NO_AI_MAPS.contains(mapId);
	}

	public static boolean isCityMap(int mapId) {
		return containsInArray(CITY_MAPS, mapId);
	}

	public static boolean isArenaMap(int mapId) {
		return containsInArray(ARENA_MAPS, mapId);
	}

	public static boolean isTestMap(int mapId) {
		return containsInArray(TEST_MAPS, mapId);
	}

	private static boolean containsInArray(int[] array, int value) {
		for (int element : array) {
			if (element == value) {
				return true;
			}
		}
		return false;
	}

	public static int getNoAiMapCount() {
		return NO_AI_MAPS.size();
	}
}
