package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.container.StatEnum;

class PhysicalAttackFunction extends StatFunction
{
	PhysicalAttackFunction() {
		stat = StatEnum.PHYSICAL_ATTACK;
	}
	
	@Override
	public void apply(Stat stat) {
		float power = stat.getOwner().getGameStats().getPower().getCurrent();
		stat.setBaseRate(power * 0.01f);
	}
	
	@Override
	public int getPriority() {
		return 30;
	}
}