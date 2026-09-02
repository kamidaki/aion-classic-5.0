package com.aionemu.gameserver.utils.stats.enums;

public enum HEALTH
{
	GLADIATOR(115),
	TEMPLAR(100),
	ASSASSIN(100),
	RANGER(100),
	SORCERER(90),
	SPIRIT_MASTER(90),
	CLERIC(110),
	CHANTER(105),
	REVENANT(100),
	BRAWLER(115),
	LUMINESS(90),
	PHOENIX(105),
	SOUL_REAPER(115);
	
	private int value;
	
	private HEALTH(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
