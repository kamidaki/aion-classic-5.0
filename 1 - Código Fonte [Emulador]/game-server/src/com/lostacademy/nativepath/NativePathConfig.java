package com.lostacademy.nativepath;

import com.aionemu.commons.configuration.Property;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Parâmetros de configuração e controle operacional do subsistema de navegação nativa.
 *
 * Agora com pré-carregamento total (100%) na inicialização do GameServer, mantendo todas as malhas
 * permanentemente residentes na memória RAM (sem carregamento sob demanda e sem evicção),
 * operando com latência zero exatamente como o subsistema GeoEngine (.geo).
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathConfig {

	/**
	 * Habilita ou desabilita globalmente o subsistema de navegação nativa CryEngine.
	 * Quando desativado, o emulador desce diretamente para o motor Eleanor ou GeoEngine Vanilla.
	 */
	@Property(key = "gameserver.nativepath.enable", defaultValue = "true")
	public static boolean NATIVE_PATH_ENABLE;

	/**
	 * Diretório base contendo as pastas indexadas de cada mapa (data/native-path/).
	 */
	@Property(key = "gameserver.nativepath.dir", defaultValue = "data/native-path/")
	public static String NATIVE_PATH_DIR;

	/**
	 * Mantido para compatibilidade de configuração (agora todos os mapas residem na memória).
	 */
	@Property(key = "gameserver.nativepath.max_cached_maps", defaultValue = "185")
	public static int NATIVE_PATH_MAX_CACHED_MAPS;

	/**
	 * Mantido para compatibilidade de configuração.
	 */
	@Property(key = "gameserver.nativepath.inactive_timeout_ms", defaultValue = "300000")
	public static long NATIVE_PATH_INACTIVE_TIMEOUT_MS;

	/**
	 * Mantido para compatibilidade de configuração.
	 */
	@Property(key = "gameserver.nativepath.cleanup_interval_ms", defaultValue = "180000")
	public static long NATIVE_PATH_CLEANUP_INTERVAL_MS;

	/**
	 * Limite de nós explorados pelo algoritmo A* antes de declarar falha de percurso.
	 */
	@Property(key = "gameserver.nativepath.max_search_nodes", defaultValue = "4000")
	public static int NATIVE_PATH_MAX_SEARCH_NODES;

	/**
	 * Habilita telemetria e registros detalhados de cálculo de rotas no console.
	 */
	@Property(key = "gameserver.nativepath.debug", defaultValue = "false")
	public static boolean NATIVE_PATH_DEBUG;

	private NativePathConfig() {
	}
}
