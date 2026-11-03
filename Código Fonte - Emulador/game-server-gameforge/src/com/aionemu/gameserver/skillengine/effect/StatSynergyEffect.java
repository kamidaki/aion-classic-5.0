package com.aionemu.gameserver.skillengine.effect;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.stats.calc.functions.IStatFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatSynergyFunction;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Passive Classic 5.0 effect that derives one or two stats from another stat.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "StatSynergyEffect")
public class StatSynergyEffect extends EffectTemplate {

	@XmlAttribute(required = true)
	private StatEnum source;
	@XmlAttribute(required = true)
	private StatEnum target;
	@XmlAttribute(name = "source_value", required = true)
	private int sourceValue;
	@XmlAttribute(name = "target_value", required = true)
	private int targetValue;
	@XmlAttribute(name = "fixed_value")
	private int fixedValue;
	@XmlAttribute
	private StatEnum target2;
	@XmlAttribute(name = "source_value2")
	private int sourceValue2;
	@XmlAttribute(name = "target_value2")
	private int targetValue2;
	@XmlAttribute(name = "fixed_value2")
	private int fixedValue2;

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}

	@Override
	public void startEffect(Effect effect) {
		List<IStatFunction> modifiers = new ArrayList<>(2);
		modifiers.add(new StatSynergyFunction(source, target, sourceValue, targetValue, fixedValue));
		if (target2 != null)
			modifiers.add(new StatSynergyFunction(source, target2, sourceValue2, targetValue2, fixedValue2));
		effect.getEffected().getGameStats().addEffect(effect, modifiers);
	}

	@Override
	public void endEffect(Effect effect) {
		effect.getEffected().getLifeStats().updateCurrentStats();
	}
}
