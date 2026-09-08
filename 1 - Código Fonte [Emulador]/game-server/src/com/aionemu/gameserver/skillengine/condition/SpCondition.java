package com.aionemu.gameserver.skillengine.condition;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Skill;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SpCondition")
public class SpCondition extends Condition {

	@XmlAttribute(required = true)
	protected int value;

	public int getValue() {
		return value;
	}

	@Override
	public boolean validate(Skill skill) {
		return true;
	}
}
