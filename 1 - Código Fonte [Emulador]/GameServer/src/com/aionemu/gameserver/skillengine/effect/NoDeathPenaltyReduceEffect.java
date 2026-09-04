package com.aionemu.gameserver.skillengine.effect;

import com.aionemu.gameserver.skillengine.model.Effect;

/****/
/** Author Rinzler (Encom)
/****/

public class NoDeathPenaltyReduceEffect extends BuffEffect
{
	public void calculate(Effect effect) {
		effect.addSucessEffect(this);
	}
	
	public void startEffect(Effect effect) {
		effect.setNoDeathPenaltyReduce(true);
	}
}