package com.aionemu.gameserver.model.templates.housing;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "PlaceLocation")
@XmlEnum
public enum PlaceLocation {

	FLOOR,
	STACK,
	WALL;

	public String value() {
		return name();
	}

	public static PlaceLocation fromValue(String value) {
		return valueOf(value);
	}

}
