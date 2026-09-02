package com.aionemu.gameserver.utils.stats.enums;

public enum WILL
{
	GLADIATOR(90),
	TEMPLAR(105),
	ASSASSIN(90),
	RANGER(90),
	SORCERER(110),
	SPIRIT_MASTER(115),
	CLERIC(110),
	CHANTER(110),
	REVENANT(100),
	BRAWLER(90),
	LUMINESS(110),
	PHOENIX(100),
	SOUL_REAPER(110);
	
	private int value;
	
	private WILL(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
