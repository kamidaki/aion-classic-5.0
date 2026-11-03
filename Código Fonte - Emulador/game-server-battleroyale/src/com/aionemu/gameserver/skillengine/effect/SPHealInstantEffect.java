package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.container.PlayerLifeStats;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.EffectReserved;
import com.aionemu.gameserver.skillengine.model.EffectReserved.ResourceType;

/**
 * Ganho de SP (energia do Revenant): EX_SP_Recover_10/20/30 pelo penalty_skill_succ dos golpes, TH_ElectricCharge, poções de SP.
 *
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SPHealInstantEffect")
public class SPHealInstantEffect extends AbstractHealEffect {

	@Override
	public void calculate(Effect effect) {
		if (!super.calculate(effect, null, null))
			return;
		// 5.0 oficial (TH_ElectricCharge_G1): o resultado leva um reserved de valor 0; o SP novo só chega no 0x14B
		effect.setReserveds(new EffectReserved(position, 0, ResourceType.HP, false), false);
	}

	@Override
	public void applyEffect(Effect effect) {
		if (!(effect.getEffected() instanceof Player player))
			return;
		int value = calculateBaseHealValue(effect);
		if (percent)
			value = PlayerLifeStats.MAX_SP * value / 100;
		player.getLifeStats().increaseSp(value);
	}

	@Override
	public int getCurrentStatValue(Effect effect) {
		return effect.getEffected() instanceof Player player ? player.getLifeStats().getCurrentSp() : 0;
	}

	@Override
	public int getMaxStatValue(Effect effect) {
		return PlayerLifeStats.MAX_SP;
	}
}
