package com.aionemu.gameserver.utils.stats.enums;

public enum KNOWLEDGE
{
	GLADIATOR(90),
	TEMPLAR(90),
	ASSASSIN(90),
	RANGER(90),
	SORCERER(120),
	SPIRIT_MASTER(115),
	CLERIC(105),
	CHANTER(105),
	REVENANT(90),
	BRAWLER(90),
	LUMINESS(120),
	PHOENIX(100),
	SOUL_REAPER(120);
	
	private int value;
	
	private KNOWLEDGE(int value) {
		this.value = value;
	}
	
	public int getValue() {
		return value;
	}
}
