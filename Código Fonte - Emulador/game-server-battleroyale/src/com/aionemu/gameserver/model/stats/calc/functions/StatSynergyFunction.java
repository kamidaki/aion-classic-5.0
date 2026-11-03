package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.stats.calc.Stat2;
import com.aionemu.gameserver.model.stats.container.CreatureGameStats;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.utils.stats.CalculationType;

/**
 * Adds a stat bonus derived from the current value of another stat.
 */
public class StatSynergyFunction extends StatFunction {

	private final StatEnum source;
	private final int sourceValue;
	private final int targetValue;
	private final int fixedValue;

	public StatSynergyFunction(StatEnum source, StatEnum target, int sourceValue, int targetValue, int fixedValue) {
		super(target, 0, true);
		if (sourceValue <= 0)
			throw new IllegalArgumentException("Stat synergy source value must be positive");
		this.source = source;
		this.sourceValue = sourceValue;
		this.targetValue = targetValue;
		this.fixedValue = fixedValue;
	}

	@Override
	public void apply(Stat2 stat, CalculationType... calculationTypes) {
		int sourceCurrent = getSourceCurrent(stat.getOwner().getGameStats());
		stat.addToBonus(calculateBonus(sourceCurrent, sourceValue, targetValue, fixedValue));
	}

	private int getSourceCurrent(CreatureGameStats<?> gameStats) {
		return switch (source) {
			case MAXHP -> gameStats.getMaxHp().getCurrent();
			case BOOST_MAGICAL_SKILL -> gameStats.getMBoost().getCurrent();
			case PHYSICAL_ATTACK -> gameStats.getMainHandPAttack().getCurrent();
			default -> throw new IllegalArgumentException("Unsupported stat synergy source: " + source);
		};
	}

	public static int calculateBonus(int sourceCurrent, int sourceValue, int targetValue, int fixedValue) {
		return fixedValue + Math.max(0, sourceCurrent) / sourceValue * targetValue;
	}

	@Override
	public int getPriority() {
		return 60;
	}
}
