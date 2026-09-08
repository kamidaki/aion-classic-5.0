package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ProcSPHealInstantEffect")
public class ProcSPHealInstantEffect extends AbstractHealEffect {

	@Override
	public void calculate(Effect effect) {
	}

	@Override
	public void applyEffect(Effect effect) {
	}

	@Override
	public int getCurrentStatValue(Effect effect) {
		return 0;
	}

	@Override
	public int getMaxStatValue(Effect effect) {
		return 0;
	}
}
