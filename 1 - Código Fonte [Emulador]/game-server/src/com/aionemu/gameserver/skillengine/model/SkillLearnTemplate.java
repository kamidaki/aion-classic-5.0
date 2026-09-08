package com.aionemu.gameserver.skillengine.model;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "skill")
public class SkillLearnTemplate {

	@XmlAttribute(name = "classId")
	private PlayerClass classId;
	@XmlAttribute(name = "skillId", required = true)
	private int skillId;
	@XmlAttribute(name = "name")
	private String name;
	@XmlAttribute(name = "skillLevel")
	private Integer skillLevel;
	@XmlAttribute(name = "skillLearn")
	private Integer skillLearn;
	@XmlAttribute(name = "race")
	private Race race = Race.PC_ALL;
	@XmlAttribute(name = "minLevel", required = true)
	private int minLevel;
	@XmlAttribute(name = "autolearn")
	private boolean autolearn;
	@XmlAttribute(name = "autoLearn")
	private Boolean autoLearn;
	@XmlAttribute
	private boolean stigma;
	@XmlAttribute(name = "skillBook")
	private boolean skillBook;

	public PlayerClass getClassId() {
		return classId;
	}

	public int getSkillId() {
		return skillId;
	}

	public String getName() {
		return name;
	}

	public int getSkillLevel() {
		if (skillLevel != null) {
			return skillLevel;
		}
		return DataManager.SKILL_DATA.getSkillTemplate(skillId).getLvl();
	}

	public int getMinLevel() {
		return minLevel;
	}

	public Race getRace() {
		return race;
	}

	public boolean isAutolearn() {
		return (autoLearn != null && autoLearn) || autolearn;
	}

	public boolean isStigma() {
		return stigma;
	}

	public boolean isSkillBook() {
		return skillBook;
	}

	public boolean isLinkedStigma() { return false; }

	/**
	 * Skill learning since 4.8 is different than before. Every level of a skill has its own skillId.<br>
	 * This method returns the skillId of the next lower level of a skill.
	 * 
	 * @return The skillId of the pre-skill to this one or {@code null} if it has no pre-skill.
	 */
	public Integer getLearnSkill() {
		return skillLearn;
	}
}
