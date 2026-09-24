package com.aionemu.gameserver.model.templates.rewards;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlSeeAlso;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.templates.QuestTemplate;
import com.aionemu.gameserver.model.templates.itemgroups.ItemRaceEntry;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "CraftReward")
@XmlSeeAlso({ CraftRecipe.class, CraftItem.class })
public abstract class CraftReward extends ItemRaceEntry {

	@XmlAttribute(name = "skill")
	private int skill;

	public int getSkill() {
		return skill;
	}

	@Override
	protected boolean matchesQuest(QuestTemplate questTemplate) {
		return questTemplate.getCombineSkill() == skill;
	}
}
