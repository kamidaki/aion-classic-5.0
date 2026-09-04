package com.aionemu.gameserver.skillengine.effect;

import com.aionemu.gameserver.skillengine.model.Effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

/****/
/** Author Rinzler (Encom)
/****/

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "EnchantBoostEffect")
public class EnchantBoostEffect extends BuffEffect
{
	@Override
	public void calculate(Effect effect) {
		effect.setEnchantBoost(true);
		effect.addSucessEffect(this);
	}
}