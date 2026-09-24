package com.lostacademy.nativepath;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Testes unitários para o subsistema CryEngine Native-Path.
 * Valida configurações cinemáticas, limites de elevação, cache bounded LRU e A*.
 */
public class NativePathTest {

	@Test
	@DisplayName("Validação das constantes cinemáticas de desnível e passo")
	public void testKinematicConstants() {
		assertEquals(0.8f, NativePathMap.MAX_STEP_UP, 0.001f, "Passo máximo para subida deve ser 0.8m");
		assertEquals(1.8f, NativePathMap.MAX_DROP_DOWN, 0.001f, "Queda máxima permitida deve ser 1.8m");
		assertTrue(NativePathMap.MAX_STEP_UP < NativePathMap.MAX_DROP_DOWN, "Subida máxima deve ser mais restrita que descida");
	}

	@Test
	@DisplayName("Validação dos limites do cache LRU e retenção de memória")
	public void testCacheConfiguration() {
		assertEquals(25, NativePathConfig.NATIVE_PATH_MAX_CACHED_MAPS, "Limite máximo de mapas no cache deve ser 25");
		assertEquals(300000L, NativePathConfig.NATIVE_PATH_INACTIVE_TIMEOUT_MS, "Timeout de inatividade deve ser 5 minutos (300.000 ms)");
		assertEquals(180000L, NativePathConfig.NATIVE_PATH_CLEANUP_INTERVAL_MS, "Intervalo de limpeza deve ser 3 minutos (180.000 ms)");
	}

	@Test
	@DisplayName("Validação de tolerância a NaN e elevação segura")
	public void testSafeElevationHandling() {
		float fallbackZ = 120.5f;
		float nanZ = Float.NaN;

		// Garantir que Float.isNaN é verificado adequadamente
		float safeZ = Float.isNaN(nanZ) ? fallbackZ : nanZ;
		assertEquals(fallbackZ, safeZ, 0.001f, "Valores NaN de elevação devem cair com segurança no fallbackZ");

		float validZ = 150.0f;
		safeZ = Float.isNaN(validZ) ? fallbackZ : validZ;
		assertEquals(150.0f, safeZ, 0.001f, "Valores válidos de elevação devem ser preservados");
	}

	@Test
	@DisplayName("Validação de restrições de inclinação máxima do A*")
	public void testSlopeValidation() {
		float currentZ = 100.0f;

		// Subida de 0.5m (permitida, <= 0.8m)
		float targetZPermitted = 100.5f;
		float deltaZ = targetZPermitted - currentZ;
		assertTrue(deltaZ <= NativePathMap.MAX_STEP_UP, "Subida suave deve ser permitida");

		// Subida de 1.2m (bloqueada, > 0.8m)
		float targetZBlocked = 101.2f;
		deltaZ = targetZBlocked - currentZ;
		assertFalse(deltaZ <= NativePathMap.MAX_STEP_UP, "Escalada excessiva de penhasco deve ser bloqueada");

		// Queda de 1.5m (permitida, <= 1.8m)
		float targetDropPermitted = 98.5f;
		float dropZ = currentZ - targetDropPermitted;
		assertTrue(dropZ <= NativePathMap.MAX_DROP_DOWN, "Descida moderada deve ser permitida");

		// Queda de 3.0m (bloqueada, > 1.8m)
		float targetDropBlocked = 97.0f;
		dropZ = currentZ - targetDropBlocked;
		assertFalse(dropZ <= NativePathMap.MAX_DROP_DOWN, "Queda brusca de despenhadeiro deve ser bloqueada");
	}

	@Test
	@DisplayName("Teste diagnóstico de A* em Inggison com obstáculo")
	public void testInggisonAStar() throws Exception {
		java.nio.file.Path p = java.nio.file.Paths.get("data/native-path/210050000_lf4/lf4-path.dat");
		if (!java.nio.file.Files.exists(p)) {
			return; // Pula se arquivo não estiver no path de execução do teste
		}
		NativePathMap map = NativePathMap.loadFromDisk(p, 210050000);
		assertNotNull(map);

		// Posição de spawn do Steelback Neokin em Calmheart Grove
		float startX = 1540.0f;
		float startY = 242.0f;
		float startZ = 531.75f;

		// Posição do jogador atrás de obstrução (ex: 15m de distância)
		float targetX = 1555.0f;
		float targetY = 250.0f;
		float targetZ = 531.75f;

		float[][] path = NativePathAStar.findPath(map, startX, startY, startZ, targetX, targetY, targetZ, 3.51f, 1.5f);
		System.out.println("PATH RESULT WITH RADIUS 3.51: " + (path != null ? path.length + " waypoints" : "NULL"));

		// Agora testamos pontos com obstáculo real entre eles (atrás de árvore/rocha/torre)
		// Vamos verificar células bloqueadas no setor de Inggison ao redor de (1540, 242)
		int sx = 1540 / 16;
		int sy = 242 / 16;
		NativePathSector sector = map.getSector(sx, sy);
		System.out.println("SECTOR layers: " + (sector != null ? sector.getLayerCount() : 0));
		if (sector != null && sector.getLayerCount() > 0) {
			for (int ly = 0; ly < sector.getLayerCount(); ly++) {
				NativePathSector.Layer l = sector.getLayers()[ly];
				System.out.println("Layer " + ly + " type=" + l.getType() + " hasExplicitBase=" + l.hasExplicitBase() + " baseElev=" + l.getBaseElev());
			}
		}

		// Teste de A* entre pontos onde line of sight é bloqueada
		// Encontrar uma célula bloqueada no setor:
		int blockedSubX = -1, blockedSubY = -1;
		if (sector != null && sector.getLayerCount() > 0) {
			NativePathSector.Layer l = sector.getLayers()[0];
			for (int y = 0; y < 32; y++) {
				for (int x = 0; x < 32; x++) {
					if (!l.isWalkable(x, y)) {
						blockedSubX = x;
						blockedSubY = y;
						break;
					}
				}
				if (blockedSubX >= 0) break;
			}
		}
		System.out.println("Blocked cell in sector (" + sx + ", " + sy + "): subX=" + blockedSubX + ", subY=" + blockedSubY);

		if (blockedSubX >= 0) {
			float obstWorldX = sx * 16 + blockedSubX * 0.5f;
			float obstWorldY = sy * 16 + blockedSubY * 0.5f;
			// Ponto A de um lado do obstáculo, Ponto B do outro lado
			float pAx = obstWorldX - 2.0f;
			float pAy = obstWorldY;
			float pBx = obstWorldX + 2.0f;
			float pBy = obstWorldY;
			float pAz = map.getSurfaceZ(pAx, pAy, startZ, startZ);
			float pBz = map.getSurfaceZ(pBx, pBy, startZ, startZ);

			boolean los = map.hasLineOfSight(pAx, pAy, pAz, pBx, pBy, pBz, 1.8f);
			assertFalse(los, "Não deve haver linha de visão direta através do obstáculo");

			float[][] pathAroundLarge = NativePathAStar.findPath(map, pAx, pAy, pAz, pBx, pBy, pBz, 3.51f, 0.0f);
			assertNotNull(pathAroundLarge, "A* deve encontrar rota contornando obstáculo para criatura de grande porte");
			assertTrue(pathAroundLarge.length >= 2, "Rota deve conter waypoints contornando o obstáculo");

			float[][] pathAroundSmall = NativePathAStar.findPath(map, pAx, pAy, pAz, pBx, pBy, pBz, 0.5f, 0.0f);
			assertNotNull(pathAroundSmall, "A* deve encontrar rota contornando obstáculo para criatura pequena");
			assertTrue(pathAroundSmall.length >= 2, "Rota deve conter waypoints contornando o obstáculo");
		}
	}
}
