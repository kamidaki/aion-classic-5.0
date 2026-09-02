package com.aionemu.gameserver.utils.stats;

import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.utils.stats.enums.*;

public class ClassStats
{
	private static String name(PlayerClass playerClass) {
		if (playerClass == null) return "GLADIATOR";
		switch (playerClass) {
			case WARRIOR:
				return "GLADIATOR";
			case SCOUT:
				return "RANGER";
			case MAGE:
				return "SORCERER";
			case PRIEST:
				return "CLERIC";
			case MONK:
			case THUNDERER:
				return "REVENANT";
			case REAPER:
				return "SOUL_REAPER";
			default:
				return playerClass.toString();
		}
	}

	public static int getMaxHpFor(PlayerClass playerClass, int level) {
		return MAXHP.valueOf(name(playerClass)).getMaxHpFor(level);
	}
	
	public static int getPowerFor(PlayerClass playerClass) {
		return POWER.valueOf(name(playerClass)).getValue();
	}
	
	public static int getHealthFor(PlayerClass playerClass) {
		return HEALTH.valueOf(name(playerClass)).getValue();
	}
	
	public static int getAgilityFor(PlayerClass playerClass) {
		return AGILITY.valueOf(name(playerClass)).getValue();
	}
	
	public static int getAccuracyFor(PlayerClass playerClass) {
		return ACCURACY.valueOf(name(playerClass)).getValue();
	}
	
	public static int getKnowledgeFor(PlayerClass playerClass) {
		return KNOWLEDGE.valueOf(name(playerClass)).getValue();
	}
	
	public static int getWillFor(PlayerClass playerClass) {
		return WILL.valueOf(name(playerClass)).getValue();
	}
	
	public static int getMainHandAttackFor(PlayerClass playerClass) {
		return MAIN_HAND_ATTACK.valueOf(name(playerClass)).getValue();
	}
	
	public static int getMainHandCritRateFor(PlayerClass playerClass) {
		return MAIN_HAND_CRITRATE.valueOf(name(playerClass)).getValue();
	}
	
	public static int getMainHandAccuracyFor(PlayerClass playerClass) {
		return MAIN_HAND_ACCURACY.valueOf(name(playerClass)).getValue();
	}
	
	public static int getWaterResistFor(PlayerClass playerClass) {
		return WATER_RESIST.valueOf(name(playerClass)).getValue();
	}
	
	public static int getWindResistFor(PlayerClass playerClass) {
		return WIND_RESIST.valueOf(name(playerClass)).getValue();
	}
	
	public static int getEarthResistFor(PlayerClass playerClass) {
		return EARTH_RESIST.valueOf(name(playerClass)).getValue();
	}
	
	public static int getFireResistFor(PlayerClass playerClass) {
		return FIRE_RESIST.valueOf(name(playerClass)).getValue();
	}
	
	public static int getMagicAccuracyFor(PlayerClass playerClass) {
		return MAGIC_ACCURACY.valueOf(name(playerClass)).getValue();
	}
	
	public static int getCritSpellFor(PlayerClass playerClass) {
		return CRIT_SPELL.valueOf(name(playerClass)).getValue();
	}
	
	public static int getSpellResistFor(PlayerClass playerClass) {
		return SPELL_RESIST.valueOf(name(playerClass)).getValue();
	}
	
	public static int getStrikeResistFor(PlayerClass playerClass) {
		return STRIKE_RESIST.valueOf(name(playerClass)).getValue();
	}
	
	public static int getEvasionFor(PlayerClass playerClass) {
		return EVASION.valueOf(name(playerClass)).getValue();
	}
	
	public static int getBlockFor(PlayerClass playerClass) {
		return BLOCK.valueOf(name(playerClass)).getValue();
	}
	
	public static int getParryFor(PlayerClass playerClass) {
		return PARRY.valueOf(name(playerClass)).getValue();
	}
	
	public static int getAttackRangeFor(PlayerClass playerClass) {
		return ATTACK_RANGE.valueOf(name(playerClass)).getValue();
	}
	
	public static int getAttackSpeedFor(PlayerClass playerClass) {
		return ATTACK_SPEED.valueOf(name(playerClass)).getValue();
	}
	
	public static int getFlySpeedFor(PlayerClass playerClass) {
		return FLY_SPEED.valueOf(name(playerClass)).getValue();
	}
	
	public static int getSpeedFor(PlayerClass playerClass) {
		return SPEED.valueOf(name(playerClass)).getValue();
	}
}