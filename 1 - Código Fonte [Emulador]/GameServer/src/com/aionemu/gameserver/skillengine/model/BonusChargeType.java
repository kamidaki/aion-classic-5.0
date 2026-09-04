package com.aionemu.gameserver.skillengine.model;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;



@XmlType(name = "bonusChargeType")
@XmlEnum
public enum BonusChargeType
{
	NONE,
	PHYSICAL,
	MAGICAL;
}