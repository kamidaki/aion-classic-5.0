package com.aionemu.gameserver.utils.stats.enums;

public enum ATTACK_SPEED
{
	GLADIATOR(1500),
	TEMPLAR(1500),
	ASSASSIN(1500),
	RANGER(1500),
	SORCERER(1500),
	SPIRIT_MASTER(1500),
	CLERIC(1500),
	CHANTER(1500),
	REVENANT(1500),
	BRAWLER(1500),
	LUMINESS(1500),
	PHOENIX(1500),
	SOUL_REAPER(1500);
	
	private int value;
	
	private ATTACK_SPEED(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
