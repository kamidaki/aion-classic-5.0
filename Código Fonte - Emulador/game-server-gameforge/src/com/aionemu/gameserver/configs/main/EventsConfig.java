package com.aionemu.gameserver.configs.main;

import java.util.Set;

import com.aionemu.commons.configuration.Property;

/**
 * @author Lost Academy Team & Durak
 */
public class EventsConfig {

	@Property(key = "gameserver.event.service.disabled_events")
	public static Set<String> DISABLED_EVENTS;

	/**
	 * Event Upgrade Arcade
	 */
	@Property(key = "gameserver.event.arcade.enable", defaultValue = "false")
	public static boolean ENABLE_EVENT_ARCADE;

	@Property(key = "gameserver.event.arcade.resume_token", defaultValue = "3")
	public static int ARCADE_RESUME_TOKEN;

	/**
	 * World Raid
	 */
	@Property(key = "gameserver.worldraid.enable", defaultValue = "true")
	public static boolean ENABLE_WORLDRAID;

	@Property(key = "gameserver.worldraid.use_spawn_msg", defaultValue = "true")
	public static boolean WORLDRAID_ENABLE_SPAWNMSG;




	/**
	 * Advent Calendar
	 */
	@Property(key = "gameserver.event.advent_calendar.enable", defaultValue = "false")
	public static boolean ENABLE_ADVENT_CALENDAR;
}
