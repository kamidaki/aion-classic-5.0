package com.aionemu.gameserver.model.templates.item;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.stats.ModifiersTemplate;

/**
 * Um nível da sinergia de encantamento (client_accumulated_enchant_effect): vale com a soma dos encantamentos >= sum.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "EnchantSynergyLevel")
public class EnchantSynergyLevel {

	@XmlAttribute(required = true)
	private int sum;
	@XmlAttribute(name = "skill_id")
	private int skillId;
	@XmlElement(required = true)
	private ModifiersTemplate modifiers;

	public int getSum() {
		return sum;
	}

	/**
	 * @return activation_skill do cliente (drop e AP, nível 60+), 0 sem skill
	 */
	public int getSkillId() {
		return skillId;
	}

	public List<StatFunction> getModifiers() {
		return modifiers.getModifiers();
	}
}
