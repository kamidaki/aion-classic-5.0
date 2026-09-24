package com.aionemu.gameserver.model.templates.item.bonuses;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "StatBonusType")
@XmlEnum
public enum StatBonusType {

	INVENTORY,
	POLISH
}
