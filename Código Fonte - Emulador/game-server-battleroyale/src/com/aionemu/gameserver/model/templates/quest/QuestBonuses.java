package com.aionemu.gameserver.model.templates.quest;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.templates.rewards.BonusType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "QuestBonuses")
public class QuestBonuses {

	@XmlAttribute(required = true)
	private BonusType type;
	@XmlAttribute
	private int level;

	public BonusType getType() {
		return type;
	}

	public int getLevel() {
		return level;
	}
}
