package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.HealType;


@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SPHealInstantEffect")
public class SPHealInstantEffect extends AbstractHealEffect {
	
	@Override
	public void calculate(Effect effect) {
		super.calculate(effect, HealType.SP);
	}

	@Override
	public void applyEffect(Effect effect) {
		super.applyEffect(effect, HealType.SP);
	}

	@Override
	protected int getCurrentStatValue(Effect effect) {
		return ((Player) effect.getEffected()).getCommonData().getSp();
	}

	@Override
	protected int getMaxStatValue(Effect effect) {
		return ((Player) effect.getEffected()).getGameStats().getMaxSp().getCurrent();
	}
}
