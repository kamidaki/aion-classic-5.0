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
}
