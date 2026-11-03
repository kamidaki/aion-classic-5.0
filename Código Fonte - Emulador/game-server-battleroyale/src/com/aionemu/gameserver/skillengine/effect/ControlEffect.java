package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Primeiro estágio das skills de Frenzy: resolve a resistência e mantém o
 * efeito ativo. O Deform encadeado aplica a transformação e o estado anormal.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ControlEffect")
public class ControlEffect extends EffectTemplate {

	@Override
	public void calculate(Effect effect) {
		super.calculate(effect, StatEnum.DEFORM_RESISTANCE, null);
	}

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}
}
