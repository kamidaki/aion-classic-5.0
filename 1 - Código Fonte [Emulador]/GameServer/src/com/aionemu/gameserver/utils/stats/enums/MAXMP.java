package com.aionemu.gameserver.utils.stats.enums;

public enum MAXMP
{
	GLADIATOR(100),
	TEMPLAR(100),
	ASSASSIN(100),
	RANGER(100),
	SORCERER(100),
	SPIRIT_MASTER(100),
	CLERIC(100),
	CHANTER(100),
	REVENANT(100),
	BRAWLER(100),
	LUMINESS(100),
	PHOENIX(100),
	SOUL_REAPER(100);
	
	private int value;
	
	private MAXMP(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
