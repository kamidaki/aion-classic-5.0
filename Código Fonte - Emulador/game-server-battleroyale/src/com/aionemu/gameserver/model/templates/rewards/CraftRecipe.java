package com.aionemu.gameserver.model.templates.rewards;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.templates.QuestTemplate;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "CraftRecipe")
public class CraftRecipe extends CraftReward {

	@XmlAttribute(name = "level", required = true)
	private int level;

	/**
	 * Gets the value of the level property.
	 */
	public int getLevel() {
		return level;
	}

	@Override
	protected boolean matchesQuest(QuestTemplate questTemplate) {
		if (!super.matchesQuest(questTemplate))
			return false;
		if (questTemplate.getCombineSkillPoint() < level)
			return false;
		if (questTemplate.getCombineSkillPoint() > getMaxLevel())
			return false;
		return true;
	}

	private int getMaxLevel() {
		return Math.min(level + 40, level / 100 * 100 + 99);
	}
}
