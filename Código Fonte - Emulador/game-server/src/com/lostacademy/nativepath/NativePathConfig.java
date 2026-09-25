package com.lostacademy.nativepath;

import com.aionemu.commons.configuration.Property;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Parâmetros de configuração e controle operacional do subsistema de navegação nativa.
 *
 * Motor primário e EXCLUSIVO de navegação e pathfinding do emulador:
 * 1. Consome diretamente as malhas de navegação nativas oficiais compiladas da CryEngine (*-path.dat).
 * 2. Gerenciamento inteligente de ciclo de vida com Cache LRU limitado e desalocação por inatividade.
 * 3. Ausência completa de fallbacks para GeoEngine Vanilla em tempo de execução.
 * 4. Resolução subcelular de 0.5m com suporte nativo a pontes, túneis e relevo tridimensional.
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathConfig {

	/**
	 * Habilita ou desabilita globalmente o subsistema de navegação nativa CryEngine (*-path.dat).
	 * Quando ativo, é o único motor oficial de percursos e colisões de agentes terrestres.
	 */
	@Property(key = "gameserver.nativepath.enable", defaultValue = "true")
	public static boolean NATIVE_PATH_ENABLE = true;

	/**
	 * Diretório base contendo as pastas indexadas de cada mapa (data/native-path/).
	 */
	@Property(key = "gameserver.nativepath.dir", defaultValue = "data/native-path/")
	public static String NATIVE_PATH_DIR = "data/native-path/";

	/**
	 * Tempo limite de inatividade em milissegundos sem jogadores antes de desalocar um mapa da RAM.
	 * Padrão: 180000ms (3 minutos conforme especificação técnica).
	 */
	@Property(key = "gameserver.nativepath.inactive_timeout_ms", defaultValue = "180000")
	public static long NATIVE_PATH_INACTIVE_TIMEOUT_MS = 180000L;

	/**
	 * Intervalo do agendador periódico de limpeza de mapas inativos da memória RAM.
	 * Padrão: 60000ms (1 minuto).
	 */
	@Property(key = "gameserver.nativepath.cleanup_interval_ms", defaultValue = "60000")
	public static long NATIVE_PATH_CLEANUP_INTERVAL_MS = 60000L;

	/**
	 * Limite máximo de nós explorados pelo algoritmo A* nativo antes de declarar falha de percurso.
	 */
	@Property(key = "gameserver.nativepath.max_search_nodes", defaultValue = "3000")
	public static int NATIVE_PATH_MAX_SEARCH_NODES = 3000;

	/**
	 * Habilita telemetria e registros detalhados de cálculo de rotas no console.
	 */
	@Property(key = "gameserver.nativepath.debug", defaultValue = "false")
	public static boolean NATIVE_PATH_DEBUG = false;

	private NativePathConfig() {
	}
}
