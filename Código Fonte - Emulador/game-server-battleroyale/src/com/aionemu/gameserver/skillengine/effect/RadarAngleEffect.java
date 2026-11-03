package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Declara ao cliente o ângulo de visão do radar. O cliente lê o valor da
 * definição da skill aprendida; não há estatística de combate correspondente.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "RadarAngleEffect")
public class RadarAngleEffect extends EffectTemplate {

	@Override
	public void applyEffect(Effect effect) {
		// Efeito passivo exclusivamente visual no cliente.
	}
}
