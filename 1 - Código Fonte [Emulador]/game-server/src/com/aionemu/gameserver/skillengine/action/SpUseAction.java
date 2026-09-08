package com.aionemu.gameserver.skillengine.action;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Skill;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SpUseAction")
public class SpUseAction extends Action {

	@XmlAttribute(required = true)
	protected int value;

	public int getValue() {
		return value;
	}

	@Override
	public boolean act(Skill skill) {
		return true;
	}

	@Override
	public boolean canAct(Skill skill) {
		return true;
	}
}
