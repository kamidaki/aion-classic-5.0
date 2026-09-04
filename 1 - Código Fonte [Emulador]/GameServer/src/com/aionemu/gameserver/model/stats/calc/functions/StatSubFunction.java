package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.stats.calc.Stat;


public class StatSubFunction extends StatFunction {

	@Override
	public void apply(Stat stat) {
		if (isBonus()) {
			stat.addToBonus(-getValue());
		}
		else {
			stat.addToBase(-getValue());
		}
	}

	@Override
	public final int getPriority() {
		return isBonus() ? 50 : 30;
	}

}
