package com.aionemu.gameserver.utils.stats.enums;

public enum FLY_SPEED
{
	GLADIATOR(9),
	TEMPLAR(9),
	ASSASSIN(9),
	RANGER(9),
	SORCERER(9),
	SPIRIT_MASTER(9),
	CLERIC(9),
	CHANTER(9),
	REVENANT(9),
	BRAWLER(9),
	LUMINESS(9),
	PHOENIX(9),
	SOUL_REAPER(9);
	
	private int value;
	
	private FLY_SPEED(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
