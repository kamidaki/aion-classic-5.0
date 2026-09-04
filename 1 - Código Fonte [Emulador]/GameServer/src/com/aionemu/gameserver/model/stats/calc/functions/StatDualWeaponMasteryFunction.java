package com.aionemu.gameserver.model.stats.calc.functions;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.skillengine.model.Effect;


public class StatDualWeaponMasteryFunction extends StatFunctionProxy {

	public StatDualWeaponMasteryFunction(Effect effect, IStatFunction statFunction) {
		super(effect, statFunction);
	}

	@Override
	public void apply(Stat stat) {
		Player player = (Player) stat.getOwner();
		if (player.getEquipment().isDualWeaponEquipped()) {
			super.apply(stat);
		}
	}
}
