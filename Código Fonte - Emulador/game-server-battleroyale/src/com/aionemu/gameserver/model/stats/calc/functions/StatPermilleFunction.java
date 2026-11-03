package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.stats.calc.Stat2;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.utils.stats.CalculationType;

/**
 * Applies a rate expressed in tenths of a percent. Classic title data stores
 * ratio attributes in this unit (for example, {@code speedratio 58} is 5.8%).
 */
public class StatPermilleFunction extends StatFunction {

	public StatPermilleFunction() {
	}

	public StatPermilleFunction(StatEnum name, int value, boolean bonus) {
		super(name, value, bonus);
	}

	@Override
	public void apply(Stat2 stat, CalculationType... calculationTypes) {
		if (isBonus()) {
			stat.addToBonus(stat.getBaseWithoutBaseRate() * getValue() / 1000f);
		} else {
			stat.setBase(stat.getBaseWithoutBaseRate() * (1 + getValue() / 1000f));
		}
	}

	@Override
	public int getPriority() {
		return isBonus() ? 50 : 20;
	}
}
