package com.aionemu.gameserver.model.templates.item;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlEnumValue;
import javax.xml.bind.annotation.XmlType;

@XmlType(name = "item_category")
@XmlEnum
public enum ItemCategory
{
	MANASTONE,
	GODSTONE,
	ENCHANTMENT,
	FLUX,
	BALIC_EMOTION,
	BALIC_MATERIAL,
	DROP_MATERIAL,
	RAWHIDE,
	SOULSTONE,
	RECIPE,
	GATHERABLE,
	GATHERABLE_BONUS,
	SWORD,
	DAGGER,
	MACE,
	ORB,
	SPELLBOOK,
	GREATSWORD,
	POLEARM,
	STAFF,
	BOW,
	SHIELD,
	JACKET,
	PANTS,
	SHOES,
	GLOVES,
	SHOULDERS,
	NECKLACE,
	EARRINGS,
	RINGS,
	HELMET,
	BELT,
	SKILLBOOK,
	STIGMA,
	COINS,
	MEDALS,
	QUEST,
	KEY,
	CRAFT_BOOST,
	COMBINATION,
	NONE,
	SHARD,
	BLADE,
	NO_ARMOR,
	CLOTHES,
	ROBE,
	LEATHER,
	CHAIN,
	PLATE,
	KEYHAMMER,
	OLDSEAL,

	// 5.0 prefix aliases
	@XmlEnumValue("1H_DAGGER")
	_1H_DAGGER,
	@XmlEnumValue("1H_GAUNTLET")
	_1H_GAUNTLET,
	@XmlEnumValue("1H_GUN")
	_1H_GUN,
	@XmlEnumValue("1H_MACE")
	_1H_MACE,
	@XmlEnumValue("1H_SWORD")
	_1H_SWORD,
	@XmlEnumValue("1H_TOOLHOE")
	_1H_TOOLHOE,
	@XmlEnumValue("2H_BLADE")
	_2H_BLADE,
	@XmlEnumValue("2H_BOOK")
	_2H_BOOK,
	@XmlEnumValue("2H_DIMENSIONSWORD")
	_2H_DIMENSIONSWORD,
	@XmlEnumValue("2H_ORB")
	_2H_ORB,
	@XmlEnumValue("2H_POLEARM")
	_2H_POLEARM,
	@XmlEnumValue("2H_RUNESWORD")
	_2H_RUNESWORD,
	@XmlEnumValue("2H_STAFF")
	_2H_STAFF,
	@XmlEnumValue("2H_SWORD")
	_2H_SWORD,
	@XmlEnumValue("2H_TOOLPICK")
	_2H_TOOLPICK,
	@XmlEnumValue("2H_TOOLROD")
	_2H_TOOLROD
}