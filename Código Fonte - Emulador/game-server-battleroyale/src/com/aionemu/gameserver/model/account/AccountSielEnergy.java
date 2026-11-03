package com.aionemu.gameserver.model.account;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.calc.StatOwner;
import com.aionemu.gameserver.model.stats.calc.functions.IStatFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatAddFunction;
import com.aionemu.gameserver.model.stats.container.StatEnum;

public final class AccountSielEnergy implements StatOwner {

	private static final Logger log = LoggerFactory.getLogger(AccountSielEnergy.class);

	private final SielEnergyType type;
	private final Timestamp chargeTime;
	private final Timestamp end;
	private final long remain;

	private final List<IStatFunction> functions = new ArrayList<>();

	public AccountSielEnergy(SielEnergyType type, Timestamp chargeTime, Timestamp end, long remain) {
		this.type = type;
		this.chargeTime = chargeTime;
		this.end = end;
		this.remain = remain;
	}

	public SielEnergyType getType() {
		return type;
	}

	public Timestamp getChargeTime() {
		return chargeTime;
	}

	public Timestamp getEnd() {
		return end;
	}

	public long getRemain() {
		return remain;
	}

	private boolean canApply() {
		long now = System.currentTimeMillis();
		return switch (type) {
			case TRIAL -> remain > 0;
			case MEMBERSHIP -> end == null || now < end.getTime();
			default -> false;
		};
	}

	public void apply(Player player) {
		if (canApply()) {
			functions.add(new StatAddFunction(StatEnum.BOOST_HUNTING_XP_RATE, 100, true));
			functions.add(new StatAddFunction(StatEnum.BOOST_GROUP_HUNTING_XP_RATE, 100, true));
			functions.add(new StatAddFunction(StatEnum.BOOST_CRAFTING_XP_RATE, 100, true));
			functions.add(new StatAddFunction(StatEnum.BOOST_GATHERING_XP_RATE, 100, true));
			player.getGameStats().addEffect(this, functions);
		}
	}

	public void end(Player player) {
		functions.clear();
		player.getGameStats().endEffect(this);
	}
}
