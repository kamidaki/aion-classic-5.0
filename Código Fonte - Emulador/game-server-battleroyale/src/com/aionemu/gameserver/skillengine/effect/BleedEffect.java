package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.controllers.attack.AttackUtil;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ATTACK_STATUS.LOG;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ATTACK_STATUS.TYPE;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.EffectReserved;
import com.aionemu.gameserver.skillengine.model.EffectReserved.ResourceType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BleedEffect")
public class BleedEffect extends AbstractOverTimeEffect {

	@Override
	public void calculate(Effect effect) {
		super.calculate(effect, StatEnum.BLEED_RESISTANCE, null);
	}

	@Override
	public void startEffect(final Effect effect) {
		int valueWithDelta = calculateBaseValue(effect);
		int finalDamage = AttackUtil.calculateMagicalOverTimeSkillResult(effect, valueWithDelta, this, false);
		int reductionRatio = effect.getEffected().getGameStats().getStat(StatEnum.BLEED_DAMAGE_REDUCE_RATIO, 0).getCurrent();
		finalDamage = applyDamageReduction(finalDamage, reductionRatio);
		effect.setReserveds(new EffectReserved(position, finalDamage, ResourceType.HP, true, false), true);
		super.startEffect(effect, AbnormalState.BLEED);
	}

	static int applyDamageReduction(int damage, int reductionRatio) {
		int clampedRatio = Math.clamp(reductionRatio, 0, 1000);
		return Math.max(1, Math.round(damage * (1000 - clampedRatio) / 1000f));
	}

	@Override
	public void endEffect(Effect effect) {
		super.endEffect(effect, AbnormalState.BLEED);
	}

	@Override
	public void onPeriodicAction(Effect effect) {
		Creature effected = effect.getEffected();
		effected.getController().onAttack(effect, TYPE.DAMAGE, effect.getReserveds(position).getValue(), false, LOG.BLEED, hopType);
		effected.getObserveController().notifyDotAttackedObservers(effect.getEffector(), effect);
	}
}
