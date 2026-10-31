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
	 * Enable NavMesh system
	 */
	@Property(key = "gameserver.geodata.nav.enable", defaultValue = "true")
	public static boolean GEO_NAV_ENABLE;

	/**
	 * NavMesh data directory
	 */
	@Property(key = "gameserver.geodata.nav.dir", defaultValue = "data/nav/")
	public static String GEO_NAV_DIR;

	/**
	 * Enable forced movement nav fallback
	 */
	@Property(key = "gameserver.geodata.forced_move.nav_fallback", defaultValue = "true")
	public static boolean FORCED_MOVE_NAV_FALLBACK;

	/**
	 * Official navigation grid (client levels/X-path.dat in data/native-path/) for NPC chase and return to spawn. The navmesh stays as
	 * fallback where the grid finds no path.
	 */
	@Property(key = "gameserver.geodata.pathdat.enable", defaultValue = "true")
	public static boolean PATHDAT_ENABLE;

	@Property(key = "gameserver.geodata.pathdat.dir", defaultValue = "data/native-path/")
	public static String PATHDAT_DIR;

	/**
	 * Split straight path segments where the interpolated height leaves the floor by more than 0.5 m (the official server sends one straight
	 * segment and the NPC visibly cuts through ramps and stairs). false = exactly as official.
	 */
	@Property(key = "gameserver.geodata.pathdat.follow_floor", defaultValue = "true")
	public static boolean PATHDAT_FOLLOW_FLOOR;

	/**
	 * Max A* nodes per search on the path.dat grid.
	 */
	@Property(key = "gameserver.geodata.pathdat.max_nodes", defaultValue = "100000")
	public static int PATHDAT_MAX_NODES;

	/**
	 * Chase: a walking route longer than this (meters) makes the target unreachable (the NPC gives up).
	 */
	@Property(key = "gameserver.geodata.pathdat.max_path_length", defaultValue = "100")
	public static float PATHDAT_MAX_PATH_LENGTH;

	/**
	 * Allow NPCs to drop from ledges (path.dat drop links). The official server does it; false = always walk (ramp/stairs).
	 */
	@Property(key = "gameserver.geodata.pathdat.allow_drop", defaultValue = "false")
	public static boolean PATHDAT_ALLOW_DROP;

}
