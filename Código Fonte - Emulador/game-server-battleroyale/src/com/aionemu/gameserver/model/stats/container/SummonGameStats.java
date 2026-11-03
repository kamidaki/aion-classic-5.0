package com.aionemu.gameserver.model.stats.container;

import com.aionemu.gameserver.model.gameobjects.Summon;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.calc.Stat2;
import com.aionemu.gameserver.model.summons.SummonMode;
import com.aionemu.gameserver.model.templates.stats.StatsTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SUMMON_UPDATE;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.stats.CalculationType;

/**
 * @author Lost Academy Team & Durak
 */
public class SummonGameStats extends CreatureGameStats<Summon> {

	public SummonGameStats(Summon owner) {
		super(owner);
	}

	@Override
	protected void onStatsChange(Effect effect) {
		updateStatsAndSpeedVisually();
	}

	public void updateStatsAndSpeedVisually() {
		updateStatsVisually();
		checkSpeedStats();
	}

	public void updateStatsVisually() {
		owner.getGameStats().updateStatInfo();
	}

	@Override
	public Stat2 getStat(StatEnum statEnum, float base, CalculationType... calculationTypes) {
		Stat2 stat = super.getStat(statEnum, base, calculationTypes);
		if (owner.getMaster() == null)
			return stat;
		switch (statEnum) {
			case MAXHP:
			case PHYSICAL_ATTACK:
			case MAGICAL_ATTACK:
			case EVASION:
			case PARRY:
			case PHYSICAL_DEFENSE:
			case MAGICAL_DEFEND:
			case MAGIC_SKILL_BOOST_RESIST:
			case MAGICAL_CRITICAL:
			case MAGICAL_RESIST:
				return getStatWithBonusRate(statEnum, stat, 0.5f);
			case PHYSICAL_CRITICAL:
				return getStatWithBonusRate(StatEnum.MAIN_HAND_CRITICAL, stat, 0.5f);
			case PHYSICAL_ACCURACY:
				return getStatWithBonusRate(StatEnum.MAIN_HAND_ACCURACY, stat, 0.5f);
			case BOOST_MAGICAL_SKILL:
			case MAGICAL_ACCURACY:
				return getStatWithBonusRate(statEnum, stat, 0.8f);
			case PARALYZE_RESISTANCE:
			case SLEEP_RESISTANCE:
			case POISON_RESISTANCE:
				if (isMagmaSpirit() || isSpirit("tempest")) {
					stat.addToBase(100);
				}
				break;
			case EARTH_RESISTANCE:
				if (isMagmaSpirit()) {
					stat.addToBase(200);
				} else if (isSpirit("wind")) {
					stat.addToBase(-200);
				}
				break;
			case FIRE_RESISTANCE:
				if (isMagmaSpirit()) {
					stat.addToBase(200);
				} else if (isSpirit("water")) {
					stat.addToBase(-200);
				}
				break;
			case WIND_RESISTANCE:
				if (isSpirit("tempest")) {
					stat.addToBase(200);
				} else if (isSpirit("earth")) {
					stat.addToBase(-200);
				}
				break;
			case WATER_RESISTANCE:
				if (isSpirit("tempest")) {
					stat.addToBase(200);
				} else if (isSpirit("fire")) {
					stat.addToBase(-200);
				}
				break;

		}
		return stat;
	}

	/**
	 * Elemental spirits are told apart by name, which is the only thing that distinguishes them. The 5.0 client renamed
	 * them to title case, so the comparison ignores case.
	 */
	private boolean isSpirit(String element) {
		String name = owner.getObjectTemplate().getName();
		return name != null && name.equalsIgnoreCase(element + " spirit");
	}

	/** The lava spirit of the 4.8 data is the magma spirit of the 5.0 client. */
	private boolean isMagmaSpirit() {
		return isSpirit("magma") || isSpirit("lava");
	}

	private Stat2 getStatWithBonusRate(StatEnum statEnum, Stat2 stat, float bonusRate) {
		Stat2 statToReturn = owner.getMaster().getGameStats().getItemStatBoost(statEnum, stat);
		statToReturn.setBonusRate(bonusRate);
		return statToReturn;
	}

	@Override
	public StatsTemplate getStatsTemplate() {
		return owner.getObjectTemplate().getStatsTemplate();
	}

	@Override
	public Stat2 getAttackSpeed() {
		return getStat(StatEnum.ATTACK_SPEED, owner.getObjectTemplate().getAttackSpeed());
	}

	@Override
	public Stat2 getMovementSpeed() {
		int bonusSpeed = 0;
		Player master = owner.getMaster();
		if (master != null && master.isFlying()) {
			bonusSpeed += 3000;
		}
		return getStat(StatEnum.SPEED, Math.round(getStatsTemplate().getRunSpeed() * 1000) + bonusSpeed);
	}

	@Override
	public Stat2 getAttackRange() {
		return getStat(StatEnum.ATTACK_RANGE, owner.getObjectTemplate().getAttackRange() * 1000);
	}

	@Override
	public Stat2 getHpRegenRate() {
		int base = (int) (owner.getLifeStats().getMaxHp() * (owner.getMode() == SummonMode.REST ? 0.05f : 0.025f));
		return getStat(StatEnum.REGEN_HP, base);
	}

	@Override
	public Stat2 getMpRegenRate() {
		throw new IllegalStateException("No mp regen for Summon");
	}

	@Override
	public void updateStatInfo() {
		Player master = owner.getMaster();
		if (master != null) {
			PacketSendUtility.sendPacket(master, new SM_SUMMON_UPDATE(owner));
		}
	}
}
