package com.aionemu.gameserver.model;

import javax.xml.bind.annotation.XmlEnum;

import com.aionemu.gameserver.model.stats.calc.PlayerStatCalculator;
import com.aionemu.gameserver.model.templates.L10n;
import com.aionemu.gameserver.model.templates.stats.StatsTemplate;

/**
 * @author Lost Academy Team & Durak
 */
@XmlEnum
public enum PlayerClass implements L10n {
	WARRIOR(0, 240000, false, 110, 110, 100, 100, 90, 90, 400, 400, 0),
	GLADIATOR(1, 240001, true, 115, 115, 100, 100, 90, 90, 440, 400, 0), // fighter
	TEMPLAR(2, 240002, true, 115, 100, 100, 100, 90, 105, 460, 400, 0), // knight
	SCOUT(3, 240003, false, 100, 100, 110, 110, 90, 90, 360, 400, 0),
	ASSASSIN(4, 240004, true, 110, 100, 110, 110, 90, 90, 360, 400, 0),
	RANGER(5, 240005, true, 100, 100, 115, 115, 90, 90, 280, 400, 0),
	MAGE(6, 240006, false, 90, 90, 95, 95, 115, 115, 260, 600, 0),
	SORCERER(7, 240007, true, 90, 90, 100, 100, 120, 110, 260, 600, 50), // wizard
	SPIRIT_MASTER(8, 240008, true, 90, 90, 100, 100, 115, 115, 280, 600, 50), // elementalist
	PRIEST(9, 240009, false, 95, 95, 100, 100, 100, 100, 360, 600, 0),
	CLERIC(10, 240010, true, 105, 110, 90, 90, 105, 110, 320, 600, 50),
	CHANTER(11, 240011, true, 110, 105, 90, 90, 105, 110, 360, 600, 0),
	MONK(12, 907565, false, 100, 100, 110, 110, 90, 90, 360, 400, 0),
	THUNDERER(13, 907566, false, 115, 100, 105, 100, 90, 100, 420, 400, 0),
	REVENANT(13, 907566, true, 115, 100, 105, 100, 90, 100, 420, 400, 0),
	STRIKER(15, 908460, false, 115, 115, 100, 100, 90, 90, 440, 400, 0),
	BRAWLER(16, 908461, true, 115, 115, 100, 100, 90, 90, 440, 400, 0),
	ORCHESTRATOR(18, 909301, false, 90, 90, 100, 100, 120, 110, 320, 520, 50),
	LUMINESS(19, 909302, false, 90, 90, 100, 100, 120, 110, 320, 520, 50),
	ENGINEER(21, 913661, false, 100, 100, 110, 110, 90, 90, 360, 400, 0),
	PHOENIX(22, 913662, true, 100, 105, 100, 105, 100, 100, 360, 400, 0),
	REAPER(24, 914615, false, 115, 115, 100, 100, 120, 110, 360, 520, 50),
	SOUL_REAPER(25, 914138, true, 115, 115, 100, 100, 120, 110, 360, 520, 50),
	ALL(26, 0, false, 100, 100, 100, 100, 100, 100, 360, 400, 0),
	// Backward-compatibility aliases
	GUNNER(22, 913662, false, 100, 105, 105, 100, 100, 100, 360, 400, 0);

	/** This id is used on client side */
	private final byte classId;

	private final int nameId;

	/** Tells whether player can create new character with this class */
	private final boolean startingClass;

	private final int idMask;

	private final int power, health, agility, accuracy, knowledge, will, healthMultiplier, willMultiplier, magicalCriticalResist;

	PlayerClass(int classId, int nameId, boolean isStartingClass, int power, int health, int agility, int accuracy, int knowledge, int will, int healthMultiplier, int willMultiplier, int magicalCriticalResist) {
		this.classId = (byte) classId;
		this.nameId = nameId;
		this.startingClass = isStartingClass;
		this.idMask = (int) Math.pow(2, classId);
		this.power = power;
		this.health = health;
		this.agility = agility;
		this.accuracy = accuracy;
		this.knowledge = knowledge;
		this.will = will;
		this.healthMultiplier = healthMultiplier;
		this.willMultiplier = willMultiplier;
		this.magicalCriticalResist = magicalCriticalResist;
	}

	public StatsTemplate createStatsTemplate(int level) {
		PlayerStatsTemplate statsTemplate = new PlayerStatsTemplate();
		statsTemplate.setMaxHp(PlayerStatCalculator.calculateMaxHp(this, level));
		statsTemplate.setMaxMp(PlayerStatCalculator.calculateMaxMp(this, level));
		statsTemplate.setBlock(PlayerStatCalculator.calculateBlockEvasionOrParry(level));
		statsTemplate.setParry(PlayerStatCalculator.calculateBlockEvasionOrParry(level));
		statsTemplate.setEvasion(PlayerStatCalculator.calculateBlockEvasionOrParry(level));
		statsTemplate.setAccuracy(PlayerStatCalculator.calculatePhysicalAccuracy(level));
		statsTemplate.setMacc(PlayerStatCalculator.calculateMagicalAccuracy(level));
		statsTemplate.setAttack(18);
		statsTemplate.setPcrit(2);
		statsTemplate.setMcrit(50);
		statsTemplate.setStrikeResist(PlayerStatCalculator.calculateStrikeResist(level));
		statsTemplate.setSpellResist(magicalCriticalResist);
		return statsTemplate;
	}

	/**
	 * Returns client-side id for this PlayerClass
	 * 
	 * @return classID
	 */
	public byte getClassId() {
		return classId;
	}

	/**
	 * Returns <tt>PlayerClass</tt> object correlating with given classId.
	 * 
	 * @param classId
	 *          - id of player class
	 * @return PlayerClass that matches the given classId. If there isn't one, {@link IllegalArgumentException} is being thrown.
	 */
	public static PlayerClass getPlayerClassById(byte classId) {
		return getPlayerClassById(classId, false);
	}

	public static PlayerClass getPlayerClassById(byte classId, boolean ignoreInvalidClassId) {
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
				return STRIKER;
			case 16:
				return BRAWLER;
			case 18:
				return ORCHESTRATOR;
			case 19:
				return LUMINESS;
			case 21:
				return ENGINEER;
			case 22:
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
				if (ignoreInvalidClassId)
					return null;
				throw new IllegalArgumentException("There is no player class with id " + classId);
		}
	}

	public static PlayerClass getPlayerClassByString(String fieldName) {
		for (PlayerClass pc : values()) {
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

	public int getL10nId() {
		return nameId;
	}

	/**
	 * @return true if this is one of starting classes ( player can create char with this class )
	 */
	public boolean isStartingClass() {
		return startingClass;
	}

	public PlayerClass getStartingClass() {
		return getStartingClassFor(this);
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
			case STRIKER:
			case BRAWLER:
				return BRAWLER;
			case ORCHESTRATOR:
			case LUMINESS:
				return LUMINESS;
			case ENGINEER:
			case PHOENIX:
			case GUNNER:
				return PHOENIX;
			case REAPER:
			case SOUL_REAPER:
				return SOUL_REAPER;
			default:
				return pc;
		}
	}

	public boolean isPhysicalClass() {
		return switch (this) {
			case WARRIOR, GLADIATOR, TEMPLAR, SCOUT, ASSASSIN, RANGER, CHANTER, REVENANT, BRAWLER, STRIKER -> true;
			default -> false;
		};
	}

	public String getIconImage() {
		return switch (this) {
			case WARRIOR -> "textures/ui/EMBLEM/icon_emblem_warrior.dds";
			case GLADIATOR -> "textures/ui/EMBLEM/icon_emblem_fighter.dds";
			case TEMPLAR -> "textures/ui/EMBLEM/icon_emblem_knight.dds";
			case SCOUT -> "textures/ui/EMBLEM/icon_emblem_scout.dds";
			case ASSASSIN -> "textures/ui/EMBLEM/icon_emblem_assassin.dds";
			case RANGER -> "textures/ui/EMBLEM/icon_emblem_ranger.dds";
			case MAGE -> "textures/ui/EMBLEM/icon_emblem_mage.dds";
			case SORCERER -> "textures/ui/EMBLEM/icon_emblem_wizard.dds";
			case SPIRIT_MASTER -> "textures/ui/EMBLEM/icon_emblem_elementalist.dds";
			case PRIEST -> "textures/ui/EMBLEM/icon_emblem_cleric.dds"; // cleric and priest images are switched in client
			case CLERIC -> "textures/ui/EMBLEM/icon_emblem_priest.dds"; // cleric and priest images are switched in client
			case CHANTER -> "textures/ui/EMBLEM/icon_emblem_chanter.dds";
			case MONK, ENGINEER -> "textures/ui/EMBLEM/Icon_emblem_Engineer.dds";
			case GUNNER -> "textures/ui/EMBLEM/Icon_emblem_Gunner.dds";
			case ORCHESTRATOR -> "textures/ui/EMBLEM/Icon_emblem_Artist.dds";
			case REVENANT, THUNDERER -> "textures/ui/EMBLEM/icon_emblem_revenant.dds";
			case BRAWLER, STRIKER -> "textures/ui/EMBLEM/icon_emblem_brawler.dds";
			case LUMINESS -> "textures/ui/EMBLEM/icon_emblem_luminess.dds";
			case PHOENIX -> "textures/ui/EMBLEM/icon_emblem_phoenix.dds";
			case SOUL_REAPER, REAPER -> "textures/ui/EMBLEM/icon_emblem_soul_reaper.dds";
			case ALL -> "";
		};
	}

	public int getPower() {
		return power;
	}

	public int getHealth() {
		return health;
	}

	public int getAgility() {
		return agility;
	}

	public int getAccuracy() {
		return accuracy;
	}

	public int getKnowledge() {
		return knowledge;
	}

	public int getWill() {
		return will;
	}

	public int getWillMultiplier() {
		return willMultiplier;
	}

	public int getHealthMultiplier() {
		return healthMultiplier;
	}

	public int getAgilityMultiplier() {
		return 310;
	}

	public int getAccuracyMultiplier() {
		return 200;
	}

	public int getNoWeaponPowerMultiplier() {
		return 70;
	}

	private class PlayerStatsTemplate extends StatsTemplate {

		@Override
		public int getPower() {
			return power;
		}

		@Override
		public int getHealth() {
			return health;
		}

		@Override
		public int getAgility() {
			return agility;
		}

		@Override
		public int getBaseAccuracy() {
			return accuracy;
		}

		@Override
		public int getKnowledge() {
			return knowledge;
		}

		@Override
		public int getWill() {
			return will;
		}

		@Override
		public float getWalkSpeed() {
			return 1.5f;
		}

		@Override
		public float getRunSpeed() {
			return 6f;
		}

		@Override
		public float getFlySpeed() {
			return 9f;
		}
	}
}
