package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.container.StatEnum;


public class StatShieldMasteryFunction extends StatRateFunction {

	public StatShieldMasteryFunction(StatEnum name, int value, boolean bonus) {
		super(name, value, bonus);
	}

	@Override
	public void apply(Stat stat) {
		Player player = (Player) stat.getOwner();
		if (player.getEquipment().isShieldEquipped())
		super.apply(stat);
	}
}
