package com.aionemu.gameserver.model.templates.rewards;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.itemgroups.ItemRaceEntry;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "IdLevelReward")
public class IdLevelReward extends ItemRaceEntry {

	@XmlAttribute(name = "level", required = true)
	private int level;

	/**
	 * Gets the value of the level property.
	 */
	public int getLevel() {
		return level;
	}

	@Override
	protected boolean matchesLevel(ItemTemplate itemTemplate, int bonusItemLevel) {
		return bonusItemLevel == 0 || level == bonusItemLevel;
	}
}
