package com.aionemu.gameserver.utils.stats.enums;

public enum MAIN_HAND_ATTACK
{
	GLADIATOR(19),
	TEMPLAR(19),
	ASSASSIN(19),
	RANGER(18),
	SORCERER(16),
	SPIRIT_MASTER(16),
	CLERIC(18),
	CHANTER(19),
	REVENANT(19),
	BRAWLER(19),
	LUMINESS(16),
	PHOENIX(18),
	SOUL_REAPER(19);
	
	private int value;
	
	private MAIN_HAND_ATTACK(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
