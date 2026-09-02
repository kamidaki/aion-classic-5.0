package com.aionemu.gameserver.utils.stats.enums;

public enum MAIN_HAND_CRITRATE
{
	GLADIATOR(2),
	TEMPLAR(2),
	ASSASSIN(3),
	RANGER(3),
	SORCERER(2),
	SPIRIT_MASTER(2),
	CLERIC(2),
	CHANTER(1),
	REVENANT(2),
	BRAWLER(2),
	LUMINESS(2),
	PHOENIX(2),
	SOUL_REAPER(2);
	
	private int value;
	
	private MAIN_HAND_CRITRATE(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
