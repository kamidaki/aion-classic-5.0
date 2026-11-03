package com.aionemu.gameserver.configs.main;

import java.util.regex.Pattern;

import com.aionemu.commons.configuration.Property;

/**
 * @author Lost Academy Team & Durak
 */
public class LegionConfig {

	/**
	 * Announcement pattern (checked when announcement is being created)
	 */
	@Property(key = "gameserver.legion.pattern", defaultValue = "[a-zA-Z ]{2,32}")
	public static Pattern LEGION_NAME_PATTERN;

	/**
	 * Self Intro pattern (checked when self intro is being changed)
	 */
	@Property(key = "gameserver.legion.selfintropattern", defaultValue = ".{1,32}")
	public static Pattern SELF_INTRO_PATTERN;

	/**
	 * Nickname pattern (checked when nickname is being changed)
	 */
	@Property(key = "gameserver.legion.nicknamepattern", defaultValue = ".{1,10}")
	public static Pattern NICKNAME_PATTERN;

	/**
	 * Sets disband legion time
	 */
	@Property(key = "gameserver.legion.disbandtime", defaultValue = "86400")
	public static int LEGION_DISBAND_TIME;

	/**
	 * Sets required kinah to create emblem
	 */
	@Property(key = "gameserver.legion.emblemrequiredkinah", defaultValue = "800000")
	public static int LEGION_EMBLEM_REQUIRED_KINAH;

	/**
	 * Produções de moeda por personagem e por dia (C_GUILD 0x13). PENDENTE_DE_COMPROVACAO: nas capturas oficiais só se chegou a 10 sem a
	 * mensagem de limite (STR_MSG_GUILD_DONATION_MAX_COUNT).
	 */
	@Property(key = "gameserver.legion.donation.dailylimit", defaultValue = "10")
	public static int LEGION_DONATION_DAILY_LIMIT;

	/**
	 * Enable/disable Legion Warehouse
	 */
	@Property(key = "gameserver.legion.warehouse", defaultValue = "true")
	public static boolean LEGION_WAREHOUSE;

	/**
	 * Enable/disable Legion Invite Other Faction
	 */
	@Property(key = "gameserver.legion.inviteotherfaction", defaultValue = "false")
	public static boolean LEGION_INVITEOTHERFACTION;

	@Property(key = "gameserver.legion.task.requirement.enable", defaultValue = "true")
	public static boolean ENABLE_GUILD_TASK_REQ;

	/**
	 * Enable/Disable legion dominion key requirement
	 */
	@Property(key = "gameserver.legion.require_key_for_stonespear_reach", defaultValue = "true")
	public static boolean REQUIRE_KEY_FOR_STONESPEAR_REACH;

	/**
	 * Min points to be reached in stonespear reach instance to account for a territory election
	 */
	@Property(key = "gameserver.legion.stonespear_reach_min_points", defaultValue = "0")
	public static int STONESPEAR_REACH_MIN_POINTS_FOR_TERRITORY;

}
