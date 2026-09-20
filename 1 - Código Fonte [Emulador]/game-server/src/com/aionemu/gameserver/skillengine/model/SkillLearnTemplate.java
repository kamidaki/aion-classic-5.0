package com.aionemu.gameserver.skillengine.model;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.skill.PlayerSkillList;

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
	@XmlAttribute(name = "blendingSources")
	private String blendingSources;

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

	public boolean isBlended() {
		return blendingSources != null && !blendingSources.isBlank();
	}

	/**
	 * The expression is a disjunction of combinations. "|" separates combinations,
	 * ";" separates required groups and "," separates alternative skill IDs in a group.
	 */
	public boolean hasBlendingSources(PlayerSkillList skillList) {
		if (!isBlended())
			return false;
		for (String combination : blendingSources.split("\\|")) {
			boolean matches = true;
			for (String group : combination.split(";")) {
				boolean groupMatches = false;
				for (String skillId : group.split(",")) {
					if (skillList.isSkillPresent(Integer.parseInt(skillId))) {
						groupMatches = true;
						break;
					}
				}
				if (!groupMatches) {
					matches = false;
					break;
				}
			}
			if (matches)
				return true;
		}
		return false;
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
