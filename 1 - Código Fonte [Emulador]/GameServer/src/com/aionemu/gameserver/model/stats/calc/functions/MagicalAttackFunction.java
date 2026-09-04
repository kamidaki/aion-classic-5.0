package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.stats.container.StatEnum;

class MagicalAttackFunction extends StatFunction {

	MagicalAttackFunction() {
		stat = StatEnum.MAGICAL_ATTACK;
	}

	@Override
    public void apply(Stat stat) {
        float knowledge = stat.getOwner().getGameStats().getKnowledge().getCurrent();
        stat.setBaseRate(knowledge * 0.01f);
    }

	@Override
	public int getPriority() {
		return 30;
	}
}