package com.aionemu.gameserver.configs.main;

import com.aionemu.commons.configuration.Property;

public class GeoDataConfig {

	/**
	 * Geodata enable
	 */
	@Property(key = "gameserver.geodata.enable", defaultValue = "true")
	public static boolean GEO_ENABLE;

	/**
	 * Enable canSee checks using geodata.
	 */
	@Property(key = "gameserver.geodata.cansee.enable", defaultValue = "true")
	public static boolean CANSEE_ENABLE;

	/**
	 * Enable Fear skill using geodata.
	 */
	@Property(key = "gameserver.geodata.fear.enable", defaultValue = "true")
	public static boolean FEAR_ENABLE;

	/**
	 * Enable Geo checks during npc movement (prevent flying mobs)
	 */
	@Property(key = "gameserver.geodata.npc.move", defaultValue = "true")
	public static boolean GEO_NPC_MOVE;

	/**
	 * Enable geo materials using skills
	 */
	@Property(key = "gameserver.geodata.materials.enable", defaultValue = "true")
	public static boolean GEO_MATERIALS_ENABLE;

	/**
	 * Show collision zone name and skill id
	 */
	@Property(key = "gameserver.geodata.materials.showdetails", defaultValue = "false")
	public static boolean GEO_MATERIALS_SHOWDETAILS;

	/**
	 * Enable geo shields
	 */
	@Property(key = "gameserver.geodata.shields.enable", defaultValue = "true")
	public static boolean GEO_SHIELDS_ENABLE;

	/**
	 */

	/**
	 */

	/**
	 * Compatibilidade com pacote nav (referência histórica Lost Academy).
	 * NavMesh legado (.nav) está desabilitado no Classic 5.0 — usa NativePath CryEngine.
	 */
	@Property(key = "gameserver.geodata.nav.enable", defaultValue = "false")
	public static boolean GEO_NAV_ENABLE;

	/**
	 * Diretório dos arquivos .nav (compatibilidade — não usado no Classic 5.0).
	 */
	@Property(key = "gameserver.geodata.nav.dir", defaultValue = "data/nav/")
	public static String GEO_NAV_DIR;

}
