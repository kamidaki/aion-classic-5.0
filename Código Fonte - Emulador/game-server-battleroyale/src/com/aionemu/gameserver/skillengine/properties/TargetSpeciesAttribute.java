package com.aionemu.gameserver.skillengine.properties;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "TargetSpeciesAttribute")
@XmlEnum
public enum TargetSpeciesAttribute {
	PC,
	NPC;
}
