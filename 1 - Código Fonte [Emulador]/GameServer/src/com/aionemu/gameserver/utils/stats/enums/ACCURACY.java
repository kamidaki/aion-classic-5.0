package com.aionemu.gameserver.utils.stats.enums;

public enum ACCURACY
{
	GLADIATOR(100),
	TEMPLAR(100),
	ASSASSIN(110),
	RANGER(115),
	SORCERER(100),
	SPIRIT_MASTER(100),
	CLERIC(90),
	CHANTER(90),
	REVENANT(100),
	BRAWLER(100),
	LUMINESS(100),
	PHOENIX(105),
	SOUL_REAPER(100);
	
	private int value;
	
	private ACCURACY(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
