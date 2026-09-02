package com.aionemu.gameserver.utils.stats.enums;

public enum MAXHP
{
	GLADIATOR(1.3393f, 48.246f, 342),
	TEMPLAR(1.3288f, 51.878f, 281),
	ASSASSIN(1.0488f, 40.38f, 222),
	RANGER(0.5f, 38.5f, 133),
	SORCERER(0.6352f, 24.852f, 112),
	SPIRIT_MASTER(1, 20.6f, 157),
	CLERIC(0.9277f, 35.988f, 229),
	CHANTER(0.9277f, 35.988f, 229),
	REVENANT(1.3393f, 48.246f, 342),
	BRAWLER(1.3393f, 48.246f, 342),
	LUMINESS(0.7554f, 29.457f, 132),
	PHOENIX(0.6352f, 24.852f, 112),
	SOUL_REAPER(1.0488f, 40.38f, 222);
	
	private float a;
	private float b;
	private int c;
	
	private MAXHP(float a, float b, int c) {
		this.a = a;
		this.b = b;
		this.c = c;
	}
	
	public int calculateHp(int level) {
		return Math.round(a * (level - 1) * (level - 1) + b * (level - 1) + c);
	}
	
	public int getMaxHpFor(int level) {
		return calculateHp(level);
	}
}
