package com.aionemu.gameserver.skillengine.effect;

import com.aionemu.gameserver.skillengine.model.Effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

/****/
/** Author Rinzler (Encom)
/****/

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "EnchantOptionBoostEffect")
public class EnchantOptionBoostEffect extends BuffEffect
{
	@Override
	public void calculate(Effect effect) {
		effect.setEnchantOptionBoost(true);
		effect.addSucessEffect(this);
	}
}