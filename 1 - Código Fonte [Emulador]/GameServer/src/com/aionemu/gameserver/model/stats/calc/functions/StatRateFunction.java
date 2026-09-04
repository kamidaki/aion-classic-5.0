package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.container.StatEnum;


public class StatRateFunction extends StatFunction {

	public StatRateFunction() {
	}

	public StatRateFunction(StatEnum name, int value, boolean bonus) {
		super(name, value, bonus);
	}
	
	@Override
	public void apply(Stat stat) {
		if (isBonus()) {
			stat.addToBonus((int) (stat.getBase() * getValue() / 100f));
		}
		else {
			stat.setBase((int) (stat.getBase() * stat.calculatePercent(getValue())));
		}
	}

	@Override
	public final int getPriority() {
		return isBonus() ? 40 : 20;
	}
	
	@Override
	public String toString() {
		return "StatRateFunction [" + super.toString() + "]";
	}

}
