package com.aionemu.gameserver.utils.stats.enums;

public enum SPEED
{
	GLADIATOR(6),
	TEMPLAR(6),
	ASSASSIN(6),
	RANGER(6),
	SORCERER(6),
	SPIRIT_MASTER(6),
	CLERIC(6),
	CHANTER(6),
	REVENANT(6),
	BRAWLER(6),
	LUMINESS(6),
	PHOENIX(6),
	SOUL_REAPER(6);
	
	private int value;
	
	private SPEED(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
