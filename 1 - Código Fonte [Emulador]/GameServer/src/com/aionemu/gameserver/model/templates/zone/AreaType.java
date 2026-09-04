package com.aionemu.gameserver.model.templates.zone;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;



@XmlType(name = "AreaType")
@XmlEnum
public enum AreaType {
	POLYGON,
	CYLINDER,
	SPHERE,
	SEMISPHERE;
}
