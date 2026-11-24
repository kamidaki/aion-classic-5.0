package com.aionemu.gameserver.skillengine.model;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "activationAttribute")
@XmlEnum
public enum ActivationAttribute {
	NONE,
	ACTIVE,
	PROVOKED,
	MAINTAIN,
	TOGGLE,
	PASSIVE,
	CHARGE
}
