/*
 * This file is part of Encom. **ENCOM FUCK OTHER SVN**
 *
 *  Encom is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Lesser Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  Encom is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Lesser Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser Public License
 *  along with Encom.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.model;

import com.aionemu.gameserver.model.gameobjects.player.Player;

import javax.xml.bind.annotation.XmlEnum;

@XmlEnum
public enum PlayerClass
{
	WARRIOR(0, false),
	GLADIATOR(1, true),
	TEMPLAR(2, true),
	SCOUT(3, false),
	ASSASSIN(4, true),
	RANGER(5, true),
	MAGE(6, false),
	SORCERER(7, true),
	SPIRIT_MASTER(8, true),
	PRIEST(9, false),
	CLERIC(10, true),
	CHANTER(11, true),
	MONK(12, false),
	THUNDERER(13, false),
	REVENANT(13, true),
	BRAWLER(15, true),
	LUMINESS(16, true),
	PHOENIX(17, true),
	REAPER(24, false),
	SOUL_REAPER(25, true),
	ALL(26);
	
	private byte classId;
	private int idMask;
	private boolean startingClass;

	private PlayerClass(int classId) {
		this(classId, false);
	}

	private PlayerClass(int classId, boolean startingClass) {
		this.classId = (byte) classId;
		this.startingClass = startingClass;
		this.idMask = (int) Math.pow(2, classId);
	}

	public byte getClassId() {
		return classId;
	}

	public static PlayerClass getPlayerClassById(byte classId) {
		switch (classId) {
			case 0:
				return WARRIOR;
			case 1:
				return GLADIATOR;
			case 2:
				return TEMPLAR;
			case 3:
				return SCOUT;
			case 4:
				return ASSASSIN;
			case 5:
				return RANGER;
			case 6:
				return MAGE;
			case 7:
				return SORCERER;
			case 8:
				return SPIRIT_MASTER;
			case 9:
				return PRIEST;
			case 10:
				return CLERIC;
			case 11:
				return CHANTER;
			case 12:
				return MONK;
			case 13:
				return REVENANT;
			case 14:
			case 15:
				return BRAWLER;
			case 16:
				return LUMINESS;
			case 17:
				return PHOENIX;
			case 24:
				return REAPER;
			case 25:
				return SOUL_REAPER;
			case 26:
				return ALL;
			default:
				for (PlayerClass pc : values()) {
					if (pc.getClassId() == classId)
						return pc;
				}
				throw new IllegalArgumentException("There is no player class with id " + classId);
		}
	}

	public boolean isStartingClass() {
		return startingClass;
	}

	public static PlayerClass getStartingClassFor(PlayerClass pc) {
		if (pc == null) {
			return ALL;
		}
		switch (pc) {
			case WARRIOR:
			case GLADIATOR:
			case TEMPLAR:
				return WARRIOR;
			case SCOUT:
			case ASSASSIN:
			case RANGER:
				return SCOUT;
			case MAGE:
			case SORCERER:
			case SPIRIT_MASTER:
				return MAGE;
			case PRIEST:
			case CLERIC:
			case CHANTER:
				return PRIEST;
			case THUNDERER:
			case MONK:
			case REVENANT:
				return REVENANT;
			case BRAWLER:
				return BRAWLER;
			case LUMINESS:
				return LUMINESS;
			case PHOENIX:
				return PHOENIX;
			case REAPER:
			case SOUL_REAPER:
				return SOUL_REAPER;
			default:
				return pc;
		}
	}

	public static PlayerClass getPlayerClassByString(String fieldName) {
		for (PlayerClass pc: values()) {
			if (pc.toString().equalsIgnoreCase(fieldName))
				return pc;
		}
		if ("WARRIOR".equalsIgnoreCase(fieldName)) return GLADIATOR;
		if ("SCOUT".equalsIgnoreCase(fieldName)) return RANGER;
		if ("MAGE".equalsIgnoreCase(fieldName)) return SORCERER;
		if ("PRIEST".equalsIgnoreCase(fieldName)) return CLERIC;
		if ("MONK".equalsIgnoreCase(fieldName) || "THUNDERER".equalsIgnoreCase(fieldName)) return REVENANT;
		if ("MARTIAL_ARTIST".equalsIgnoreCase(fieldName) || "BATTLE_MASTER".equalsIgnoreCase(fieldName)) return BRAWLER;
		if ("GUNNER".equalsIgnoreCase(fieldName) || "ENGINEER".equalsIgnoreCase(fieldName)) return PHOENIX;
		if ("REAPER".equalsIgnoreCase(fieldName) || "RUNEBLADE".equalsIgnoreCase(fieldName)) return SOUL_REAPER;
		return null;
	}

	public int getMask() {
		return idMask;
	}

	public String getClassType(Player player) {
		String type = null;
		switch (player.getPlayerClass()) {
			case WARRIOR:
			case RANGER:
			case CHANTER:
			case TEMPLAR:
			case ASSASSIN:
			case GLADIATOR:
			case REVENANT:
			case BRAWLER:
				type = "PHYSICAL";
			break;
			case MAGE:
			case PRIEST:
			case CLERIC:
			case SORCERER:
			case SPIRIT_MASTER:
			case LUMINESS:
			case PHOENIX:
			case SOUL_REAPER:
				type = "MAGICAL";
			break;
			default: break;
		}
		return type;
	}
}