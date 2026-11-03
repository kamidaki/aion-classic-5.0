package com.aionemu.gameserver.model.templates.teleport;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "type")
@XmlEnum
public enum TeleportType {
	REGULAR,
	FLIGHT
}
