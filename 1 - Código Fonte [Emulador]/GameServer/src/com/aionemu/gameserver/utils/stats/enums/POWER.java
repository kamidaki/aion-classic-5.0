package com.aionemu.gameserver.utils.stats.enums;

public enum POWER
{
	GLADIATOR(115),
	TEMPLAR(115),
	ASSASSIN(110),
	RANGER(100),
	SORCERER(90),
	SPIRIT_MASTER(90),
	CLERIC(105),
	CHANTER(110),
	REVENANT(115),
	BRAWLER(115),
	LUMINESS(90),
	PHOENIX(100),
	SOUL_REAPER(115);
	
	private int value;
	
	private POWER(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
