package com.aionemu.gameserver.skillengine.condition;

import com.aionemu.gameserver.skillengine.effect.AbnormalState;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.Skill;

import javax.xml.bind.annotation.XmlAttribute;


public class AbnormalStateCondition extends Condition {

	@XmlAttribute(required = true)
	protected AbnormalState value;

	/*
	 * (non-Javadoc)
	 * @see
	 * com.aionemu.gameserver.skillengine.condition.Condition#validate(com.aionemu.gameserver.skillengine.model.Skill)
	 */
	@Override
	public boolean validate(Skill env) {
		return env.getFirstTarget() != null && (env.getFirstTarget().getEffectController().isAbnormalSet(value));
	}

	@Override
	public boolean validate(Effect effect) {
		return effect.getEffected() != null && (effect.getEffected().getEffectController().isAbnormalSet(value));
	}

}
