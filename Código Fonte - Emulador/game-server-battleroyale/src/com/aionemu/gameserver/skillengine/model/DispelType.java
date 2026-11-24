package com.aionemu.gameserver.skillengine.model;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "DispelType")
@XmlEnum
public enum DispelType {

	EFFECTID,
	EFFECTIDRANGE,
	EFFECTTYPE,
	SLOTTYPE;

}
