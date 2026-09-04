package com.aionemu.gameserver.model.stats.container;

import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.gameobjects.Summon;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.templates.stats.SummonStatsTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.S_ACTION;
import com.aionemu.gameserver.network.aion.serverpackets.S_CHANGE_PET_STATUS;
import com.aionemu.gameserver.taskmanager.tasks.PacketBroadcaster.BroadcastMode;
import com.aionemu.gameserver.utils.PacketSendUtility;


public class SummonGameStats extends CreatureGameStats<Summon> {

	private int cachedSpeed;
	private final SummonStatsTemplate statsTemplate;

	/**
	 * @param owner
	 * @param statsTemplate
	 */
	public SummonGameStats(Summon owner, SummonStatsTemplate statsTemplate) {
		super(owner);
		this.statsTemplate = statsTemplate;
	}

	@Override
	protected void onStatsChange() {
		updateStatsAndSpeedVisually();
	}

	public void updateStatsAndSpeedVisually() {
		updateStatsVisually();
		checkSpeedStats();
	}

	public void updateStatsVisually() {
		owner.addPacketBroadcastMask(BroadcastMode.UPDATE_STATS);
	}

	private void checkSpeedStats() {
		int current = getMovementSpeed().getCurrent();
		if (current != cachedSpeed) {
			owner.addPacketBroadcastMask(BroadcastMode.UPDATE_SPEED);
		}
		cachedSpeed = current;
	}

	@Override
    public Stat getAllSpeed() {
        return getStat(StatEnum.ALLSPEED, 7500);
    }

	@Override
	public Stat getStat(StatEnum statEnum, int base) {
		Stat stat = super.getStat(statEnum, base);
		if (owner.getMaster() == null) {
			return stat;
		} switch (statEnum) {
			case MAXHP:
				stat.setBonusRate(0.5f);
				return owner.getMaster().getGameStats().getItemStatBoost(statEnum, stat);
			case BOOST_MAGICAL_SKILL:
			case MAGICAL_ACCURACY:
				stat.setBonusRate(0.8f);
				return owner.getMaster().getGameStats().getItemStatBoost(statEnum, stat);
			case PHYSICAL_DEFENSE:
				stat.setBonusRate(0.3f);
				return owner.getMaster().getGameStats().getItemStatBoost(statEnum, stat);
			case EVASION:
            case PARRY:
            case MAGICAL_RESIST:
            case MAGICAL_CRITICAL:
				stat.setBonusRate(0.5f);
				return owner.getMaster().getGameStats().getItemStatBoost(statEnum, stat);
			case PHYSICAL_ACCURACY:
				stat.setBonusRate(0.5f);
				owner.getMaster().getGameStats().getItemStatBoost(StatEnum.MAIN_HAND_ACCURACY, stat);
				return owner.getMaster().getGameStats().getItemStatBoost(statEnum, stat);
			case PHYSICAL_CRITICAL:
				stat.setBonusRate(0.5f);
				owner.getMaster().getGameStats().getItemStatBoost(StatEnum.MAIN_HAND_CRITICAL, stat);
				return owner.getMaster().getGameStats().getItemStatBoost(statEnum, stat);
		}
		return stat;
	}

	@Override
	public Stat getMaxHp() {
		return getStat(StatEnum.MAXHP, statsTemplate.getMaxHp());
	}
	@Override
	public Stat getMaxMp() {
		return getStat(StatEnum.MAXHP, statsTemplate.getMaxMp());
	}
	@Override
    public Stat getStrikeResist() {
        return getStat(StatEnum.PHYSICAL_CRITICAL_RESIST, 0);
    }
	@Override
    public Stat getStrikeFort() {
        return getStat(StatEnum.PHYSICAL_CRITICAL_DAMAGE_REDUCE, 0);
    }
	@Override
    public Stat getSpellResist() {
        return getStat(StatEnum.MAGICAL_CRITICAL_RESIST, 0);
    }
	@Override
    public Stat getSpellFort() {
        return getStat(StatEnum.MAGICAL_CRITICAL_DAMAGE_REDUCE, 0);
    }
	@Override
    public Stat getBCastingTime() {
        return getStat(StatEnum.BOOST_CASTING_TIME, 1000);
    }
	@Override
	public Stat getConcentration() {
        return getStat(StatEnum.CONCENTRATION, 0);
    }
	@Override
	public Stat getRootResistance() {
        return getStat(StatEnum.ROOT_RESISTANCE, 0);
    }
	@Override
	public Stat getSnareResistance() {
        return getStat(StatEnum.SNARE_RESISTANCE, 0);
    }
	@Override
	public Stat getBindResistance() {
        return getStat(StatEnum.BIND_RESISTANCE, 0);
    }
	@Override
	public Stat getFearResistance() {
        return getStat(StatEnum.FEAR_RESISTANCE, 0);
    }
	@Override
	public Stat getSleepResistance() {
        return getStat(StatEnum.SLEEP_RESISTANCE, 0);
    }

	@Override
	public Stat getMainHandMAccuracy(){
		return getStat(StatEnum.MAGICAL_ACCURACY, this.statsTemplate.getMagicAccuracy());
	}

	@Override
	public Stat getAttackSpeed() {
		return getStat(StatEnum.ATTACK_SPEED, owner.getObjectTemplate().getAttackDelay());
	}

	@Override
    public Stat getMovementSpeed() {
        int bonusSpeed = 0;
        Player master = owner.getMaster();
        if (master != null && (master.isInFlyingState() || master.isInState(CreatureState.GLIDING))) {
            bonusSpeed += 3000;
        }
        return getStat(StatEnum.SPEED, Math.round(statsTemplate.getRunSpeed() * 1000) + bonusSpeed);
    }

	@Override
	public Stat getAttackRange() {
		return getStat(StatEnum.ATTACK_RANGE, owner.getObjectTemplate().getAttackRange() * 1500);
	}

	@Override
	public Stat getPDef() {
		return getStat(StatEnum.PHYSICAL_DEFENSE, statsTemplate.getPdefense());
	}

    @Override
	public Stat getMDef() {
		return getStat(StatEnum.MAGICAL_DEFEND, 0);
	}

	@Override
	public Stat getMResist() {
		return getStat(StatEnum.MAGICAL_RESIST, statsTemplate.getMresist());
	}

    @Override
	public Stat getMBResist() {
		int base = 0;
		return getStat(StatEnum.MAGIC_SKILL_BOOST_RESIST, base);
	}

	@Override
	public Stat getPower() {
		return getStat(StatEnum.POWER, 100);
	}

	@Override
	public Stat getHealth() {
		return getStat(StatEnum.HEALTH, 100);
	}

	@Override
	public Stat getAccuracy() {
		return getStat(StatEnum.PHYSICAL_ACCURACY, 100);
	}

	@Override
	public Stat getAgility() {
		return getStat(StatEnum.AGILITY, 100);
	}

	@Override
	public Stat getKnowledge() {
		return getStat(StatEnum.KNOWLEDGE, 100);
	}

	@Override
	public Stat getWill() {
		return getStat(StatEnum.WILL, 100);
	}

	@Override
	public Stat getEvasion() {
		return getStat(StatEnum.EVASION, statsTemplate.getEvasion());
	}

	@Override
	public Stat getParry() {
		return getStat(StatEnum.PARRY, statsTemplate.getParry());
	}

	@Override
	public Stat getBlock() {
		return getStat(StatEnum.BLOCK, statsTemplate.getBlock());
	}

	@Override
	public Stat getMainHandPAttack() {
		return getStat(StatEnum.PHYSICAL_ATTACK, statsTemplate.getMainHandAttack());
	}

	@Override
	public Stat getMainHandPCritical() {
		return getStat(StatEnum.PHYSICAL_CRITICAL, statsTemplate.getMainHandCritRate());
	}

	@Override
	public Stat getMainHandPAccuracy() {
		return getStat(StatEnum.PHYSICAL_ACCURACY, statsTemplate.getMainHandAccuracy());
	}

	@Override
	public Stat getMAttack() {
		return getStat(StatEnum.MAGICAL_ATTACK, 100);
	}

	@Override
	public Stat getMainHandMAttack() {
		return getStat(StatEnum.MAGICAL_ATTACK, 100);
	}

	@Override
	public Stat getOffHandMAttack(){
		return getStat(StatEnum.MAGICAL_ATTACK,0);
	}

	@Override
	public Stat getMBoost() {
        return getStat(StatEnum.BOOST_MAGICAL_SKILL, 0);
	}

	@Override
	public Stat getMAccuracy() {
		return getStat(StatEnum.MAGICAL_ACCURACY, this.statsTemplate.getMagicAccuracy());
	}

	@Override
	public Stat getMCritical() {
		return getStat(StatEnum.MAGICAL_CRITICAL, statsTemplate.getMcrit());
	}

	@Override
	public Stat getHpRegenRate() {
		int base = (int) (owner.getLifeStats().getMaxHp() * owner.getMode().getId() == 2 ? 0.05f : 0.025f);
		return getStat(StatEnum.REGEN_HP, base);
	}

	@Override
	public Stat getMpRegenRate() {
		throw new IllegalStateException("No mp regen for Summon");
	}

	@Override
	public void updateStatInfo() {
		Player master = owner.getMaster();
		if (master != null) {
			PacketSendUtility.sendPacket(master, new S_CHANGE_PET_STATUS(owner));
		}
	}

	@Override
	public void updateSpeedInfo() {
		PacketSendUtility.broadcastPacket(owner, new S_ACTION(owner, EmotionType.START_EMOTE2, 0, 0));
	}
}