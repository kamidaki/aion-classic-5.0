package com.aionemu.gameserver.model.templates.fly;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlRootElement;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.drop.Drop;
import com.aionemu.gameserver.model.drop.FlyRewardType;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;

@XmlRootElement(name = "drop")
@XmlAccessorType(XmlAccessType.FIELD)
public class FlyDropTemplate {

	@XmlAttribute(name = "type", required = true)
	private FlyRewardType type;

	@XmlAttribute(name = "item_id", required = true)
	private int itemId;

	@XmlAttribute(name = "chance")
	private float chance = 100f;

	@XmlAttribute(name = "min_amount")
	private int minAmount = 1;

	@XmlAttribute(name = "max_amount")
	private int maxAmount = 1;

	@XmlAttribute(name = "min_player_level")
	private int minPlayerLevel = 1;

	@XmlAttribute(name = "max_player_level")
	private int maxPlayerLevel = 79;

	@XmlAttribute(name = "recommended_level")
	private int recommendedLevel;

	void afterUnmarshal(Unmarshaller u, Object parent) {
		if (minPlayerLevel <= 0)
			minPlayerLevel = 1;
		if (maxPlayerLevel < minPlayerLevel)
			maxPlayerLevel = minPlayerLevel;
	}

	public FlyRewardType getType() {
		return type;
	}

	public int getItemId() {
		return itemId;
	}

	public float getChance() {
		return chance;
	}

	public int getMinAmount() {
		return minAmount;
	}

	public int getMaxAmount() {
		return maxAmount;
	}

	public int getMinPlayerLevel() {
		return minPlayerLevel;
	}

	public int getMaxPlayerLevel() {
		return maxPlayerLevel;
	}

	public int getRecommendedLevel() {
		return recommendedLevel;
	}

	public boolean isEligibleForLevel(int playerLevel) {
		return playerLevel >= minPlayerLevel && playerLevel <= maxPlayerLevel;
	}

	public Drop toDrop() {
		return new Drop(itemId, minAmount, maxAmount, chance);
	}

	public Drop toDrop(float chanceOverride) {
		float finalChance = chanceOverride > 0 ? chanceOverride : chance;
		return new Drop(itemId, minAmount, maxAmount, finalChance);
	}

	public int resolveEffectiveLevel(int playerLevel) {
		ItemTemplate template = DataManager.ITEM_DATA.getItemTemplate(itemId);
		int baseLevel = template != null ? template.getLevel() : minPlayerLevel;
		int effectiveLevel = recommendedLevel > 0 ? recommendedLevel : baseLevel;
		effectiveLevel = Math.min(effectiveLevel, maxPlayerLevel);
		effectiveLevel = Math.min(effectiveLevel, playerLevel);
		return Math.max(minPlayerLevel, effectiveLevel);
	}
}
