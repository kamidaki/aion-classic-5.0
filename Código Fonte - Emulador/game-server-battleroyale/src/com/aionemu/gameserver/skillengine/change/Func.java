package com.aionemu.gameserver.skillengine.change;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "Func")
@XmlEnum
public enum Func {
	ADD,
	PERCENT,
	REPLACE
}
