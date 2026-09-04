package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.calc.StatOwner;
import com.aionemu.gameserver.model.stats.container.StatEnum;


public interface IStatFunction extends Comparable<IStatFunction>{

	StatEnum getName();

	boolean isBonus();

	int getPriority();

	int getValue();

	boolean validate(Stat stat, IStatFunction statFunction);

	void apply(Stat stat);
	
	StatOwner getOwner();
	
	boolean hasConditions();
}
