package com.aionemu.gameserver.configs.main;

import org.quartz.CronExpression;

import com.aionemu.commons.configuration.Property;

/**
 * @author Lost Academy Team & Durak
 */
public class AutoGroupConfig {

	@Property(key = "gameserver.autogroup.enable", defaultValue = "true")
	public static boolean AUTO_GROUP_ENABLE;

	@Property(key = "gameserver.startTime.enable", defaultValue = "true")
	public static boolean START_TIME_ENABLE;

	@Property(key = "gameserver.dredgion.registration_period", defaultValue = "120")
	public static long DREDGION_REGISTRATION_PERIOD;

	@Property(key = "gameserver.dredgion.time", defaultValue = "\"0 0 0,12,18 ? * *\"")
	public static CronExpression[] DREDGION_TIMES;

	@Property(key = "gameserver.chantra.registration_period", defaultValue = "120")
	public static long CHANTRA_REGISTRATION_PERIOD;

	@Property(key = "gameserver.chantra.time", defaultValue = "\"0 0 12,17,23 ? * FRI,SAT,SUN\"")
	public static CronExpression[] CHANTRA_TIMES;

	@Property(key = "gameserver.tiarkh_lab.registration_period", defaultValue = "120")
	public static long TIARKH_LAB_REGISTRATION_PERIOD;

	@Property(key = "gameserver.tiarkh_lab.time", defaultValue = "\"0 0 12,17,23 ? * TUE,THU\"")
	public static CronExpression[] TIARKH_LAB_TIMES;

	@Property(key = "gameserver.dranium_battlefield.registration_period", defaultValue = "120")
	public static long DRANIUM_BATTLEFIELD_REGISTRATION_PERIOD;

	@Property(key = "gameserver.dranium_battlefield.time", defaultValue = "\"0 0 12,17,23 ? * MON,WED\"")
	public static CronExpression[] DRANIUM_BATTLEFIELD_TIMES;

	@Property(key = "gameserver.sonsara.registration_period", defaultValue = "180")
	public static long SONSARA_REGISTRATION_PERIOD;

	@Property(key = "gameserver.sonsara.time", defaultValue = "\"0 0 19 ? * *\"")
	public static CronExpression[] SONSARA_TIMES;

	@Property(key = "gameserver.autogroup.announce_battleground_registrations", defaultValue = "false")
	public static boolean ANNOUNCE_BATTLEGROUND_REGISTRATIONS;
}
