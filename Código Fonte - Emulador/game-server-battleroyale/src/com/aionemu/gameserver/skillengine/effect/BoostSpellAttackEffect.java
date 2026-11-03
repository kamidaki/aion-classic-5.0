package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BoostSpellAttackEffect")
public class BoostSpellAttackEffect extends BufEffect {

	@Override
	public void endEffect(Effect effect) {
		super.endEffect(effect);
		int skillId = effect.getSkillId();
		if (skillId == 9186 || skillId == 9188 || skillId == 9190) {
			if (effect.getEffected() != null && effect.getEffected().getEffectController() != null) {
				effect.getEffected().getEffectController().removeEffect(9185);
				effect.getEffected().getEffectController().removeEffect(9187);
				effect.getEffected().getEffectController().removeEffect(9189);
			}
		}
	}
}
