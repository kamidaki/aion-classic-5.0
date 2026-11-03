package com.aionemu.gameserver.skillengine.model;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "DispelSlotType")
@XmlEnum
public enum DispelSlotType {

	BUFF,
	DEBUFF,
	SPECIAL2,
	SPEC2;

}
