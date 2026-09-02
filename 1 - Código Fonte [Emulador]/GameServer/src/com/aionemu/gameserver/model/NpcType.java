package com.aionemu.gameserver.model;

public enum NpcType
{
	NULL(-1),
	ATTACKABLE(0),
	PEACE(2),
	AGGRESSIVE(8),
	INVULNERABLE(10),
	NON_ATTACKABLE(38),
	SUPPORT(54),
	GENERAL(0),
	GUARD(0),
	SUMMON_PET(0),
	ABYSS_GUARD(0),
	MONSTER(0),
	RAID_MONSTER(0),
	HOUSING(0),
	FLAG(0),
	NORMAL(0);
	
	private int someClientSideId;
	
	private NpcType(int id) {
		this.someClientSideId = id;
	}
	
	public int getId() {
		return someClientSideId;
	}
}