package com.aionemu.gameserver.model.templates.pet;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

@XmlType(name = "FoodType")
@XmlEnum
public enum FoodType
{
	AETHER_CRYSTAL_BISCUIT,
    AETHER_GEM_BISCUIT,
    AETHER_POWDER_BISCUIT,
    ARMOR,
    BALAUR_SCALES,
    BONES,
    EXCLUDES,
    FLUIDS,
	HIGH_CRAFT_STEP,
    HEALTHY_FOOD_ALL,
    HEALTHY_FOOD_SPICY,
	INFERNAL_DIABOL_AP,
	INNOCENT_MEREK_XP,
    MISCELLANEOUS,
	NEW_YEAR_PET_FOOD,
    POPPY_SNACK,
    POPPY_SNACK_TASTY,
    POPPY_SNACK_NUTRITIOUS,
	SHUGO_COIN,
    SOULS,
    STINKY,
    THORNS;
	
	public String value() {
		return name();
	}
	
	public static FoodType fromValue(String value) {
		return valueOf(value);
	}
}