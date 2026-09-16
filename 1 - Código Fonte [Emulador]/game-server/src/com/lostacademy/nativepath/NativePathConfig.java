package com.lostacademy.nativepath;

import com.aionemu.commons.configuration.Property;

/**
 * Configurações para o subsistema de navegação nativa CryEngine (native-path).
 *
 * @author KAMIDAKI
 */
public final class NativePathConfig {

	@Property(key = "gameserver.nativepath.enable", defaultValue = "true")
	public static boolean NATIVE_PATH_ENABLE;

	@Property(key = "gameserver.nativepath.dir", defaultValue = "data/native-path/")
	public static String NATIVE_PATH_DIR;

	@Property(key = "gameserver.nativepath.max_cached_maps", defaultValue = "15")
	public static int NATIVE_PATH_MAX_CACHED_MAPS;

	@Property(key = "gameserver.nativepath.inactive_timeout_ms", defaultValue = "300000")
	public static long NATIVE_PATH_INACTIVE_TIMEOUT_MS;

	@Property(key = "gameserver.nativepath.cleanup_interval_ms", defaultValue = "180000")
	public static long NATIVE_PATH_CLEANUP_INTERVAL_MS;

	@Property(key = "gameserver.nativepath.max_search_nodes", defaultValue = "4000")
	public static int NATIVE_PATH_MAX_SEARCH_NODES;

	@Property(key = "gameserver.nativepath.debug", defaultValue = "false")
	public static boolean NATIVE_PATH_DEBUG;

	private NativePathConfig() {
	}
}
