package com.aionemu.gameserver.skillengine.condition;

import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.calc.StatCondition;
import com.aionemu.gameserver.model.stats.calc.functions.IStatFunction;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.Skill;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;


@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Condition")
public abstract class Condition implements StatCondition {

	/**
	 * Validate condition specified in template
	 * 
	 * @param env
	 * @return true or false
	 */
	public abstract boolean validate(Skill env);

	@Override
	public boolean validate(Stat stat, IStatFunction statFunction) {
		return true;
	}

	public boolean validate(Effect effect) {
		return true;
	}

}
