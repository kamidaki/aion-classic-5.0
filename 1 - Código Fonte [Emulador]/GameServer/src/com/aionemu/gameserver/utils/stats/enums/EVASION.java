package com.aionemu.gameserver.utils.stats.enums;

public enum EVASION
{
	GLADIATOR(0),
	TEMPLAR(0),
	ASSASSIN(0),
	RANGER(0),
	SORCERER(0),
	SPIRIT_MASTER(0),
	CLERIC(0),
	CHANTER(0),
	REVENANT(0),
	BRAWLER(0),
	LUMINESS(0),
	PHOENIX(0),
	SOUL_REAPER(0);
	
	private int value;
	
	private EVASION(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
