package com.aionemu.gameserver.skillengine.properties;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "TargetRelationAttribute")
@XmlEnum
public enum TargetRelationAttribute {

	NONE,
	ENEMY,
	MYPARTY,
	ALL,
	FRIEND
}
