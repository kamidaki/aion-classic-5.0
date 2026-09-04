package com.aionemu.chatserver.model;

public enum PlayerClass
{
	WARRIOR(0),
	GLADIATOR(1),
	TEMPLAR(2),
	SCOUT(3),
	ASSASSIN(4),
	RANGER(5),
	MAGE(6),
	SORCERER(7),
	SPIRIT_MASTER(8),
	PRIEST(9),
	CLERIC(10),
	CHANTER(11),
	MONK(12),
	THUNDERER(13),
	REVENANT(13),
	BRAWLER(15),
	LUMINESS(16),
	PHOENIX(17),
	REAPER(24),
	SOUL_REAPER(25),
	ALL(26);
	
	private byte classId;
	
	private PlayerClass(int classId) {
		this.classId = (byte) classId;
	}
	
	public byte getClassId() {
		return classId;
	}

	public static PlayerClass getPlayerClassById(byte classId) {
		for (PlayerClass pc : values()) {
			if (pc.getClassId() == classId)
				return pc;
		}
		return ALL;
	}
}