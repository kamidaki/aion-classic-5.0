package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.EffectReserved;
import com.aionemu.gameserver.skillengine.model.EffectReserved.ResourceType;

/**
 * Ganho de EP (Ki do Brawler). No cliente é ClassPointHeal_Instant com reserved3=EP: EP_Recover_10..50 disparados pelo penalty_skill_succ dos golpes,
 * ST_recover e ST_SuperRecover. Ao chegar a 100 entra o Fever (ver {@link com.aionemu.gameserver.model.stats.container.PlayerLifeStats#increaseEp}).
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ClassPointHealInstantEffect")
public class ClassPointHealInstantEffect extends EffectTemplate {

	@Override
	public void calculate(Effect effect) {
		if (!super.calculate(effect, null, null))
			return;
		// 5.0 oficial: o resultado leva um reserved de valor 0; o EP novo só chega no 0x175
		effect.setReserveds(new EffectReserved(position, 0, ResourceType.HP, false), false);
	}

	@Override
	public void applyEffect(Effect effect) {
		if (effect.getEffected() instanceof Player player)
			player.getLifeStats().increaseEp(calculateBaseValue(effect));
	}
}
