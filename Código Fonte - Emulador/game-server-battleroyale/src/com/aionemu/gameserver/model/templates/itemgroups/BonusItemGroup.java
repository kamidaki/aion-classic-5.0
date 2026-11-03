package com.aionemu.gameserver.model.templates.itemgroups;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlSeeAlso;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.Chance;
import com.aionemu.gameserver.model.templates.rewards.BonusType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BonusItemGroup")
@XmlSeeAlso({ CraftItemGroup.class, CraftRecipeGroup.class, EventGroup.class, ManastoneGroup.class, FoodGroup.class, MedicineGroup.class,
	OreGroup.class, GatherGroup.class, EnchantGroup.class, BossGroup.class })
public abstract class BonusItemGroup implements Chance {

	@XmlAttribute(name = "bonusType", required = true)
	protected BonusType bonusType;

	@XmlAttribute(name = "chance")
	protected float chance = 100f;

	public BonusType getBonusType() {
		return bonusType;
	}

	@Override
	public float getChance() {
		return chance;
	}

	public abstract List<? extends ItemRaceEntry> getItems();

}
