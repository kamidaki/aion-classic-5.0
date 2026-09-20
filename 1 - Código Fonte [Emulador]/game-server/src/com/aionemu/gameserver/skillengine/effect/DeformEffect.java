package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "DeformEffect")
public class DeformEffect extends TransformEffect {

	@Override
	public void applyEffect(Effect effect) {
		super.applyEffect(effect);
	}

	@Override
	public void calculate(Effect effect) {
		super.calculate(effect, StatEnum.DEFORM_RESISTANCE, null);
	}

	@Override
	public void startEffect(Effect effect) {
		// Some Classic effects (for example WI_Sleep_G1) use Deform only as an
		// abnormal state and explicitly declare no model. Do not reset an active
		// transformation when the client definition has no visual model.
		if (model > 0)
			super.startEffect(effect);
		effect.getEffected().getEffectController().setAbnormal(AbnormalState.DEFORM);
		effect.setAbnormal(AbnormalState.DEFORM);
	}

	@Override
	public void endEffect(Effect effect) {
		if (model > 0)
			super.endEffect(effect);
		effect.getEffected().getEffectController().unsetAbnormal(AbnormalState.DEFORM);
	}
}
