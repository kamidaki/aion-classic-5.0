package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Marca a passiva que habilita o Quick Glide. A ativação e a velocidade são
 * tratadas pelo FlyController quando o cliente envia FLY_SPRINT.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "FlyBoostEffect")
public class FlyBoostEffect extends EffectTemplate {

	@Override
	public void applyEffect(Effect effect) {
		// A presença da skill aprendida é o estado persistente consultado pelo controlador.
	}
}
