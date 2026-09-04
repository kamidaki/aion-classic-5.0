package com.aionemu.gameserver.model.templates.staticdoor;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;


@XmlType(name = "DoorType")
@XmlEnum
public enum DoorType {
	DOOR,
	ABYSS,
	HOUSE
}
