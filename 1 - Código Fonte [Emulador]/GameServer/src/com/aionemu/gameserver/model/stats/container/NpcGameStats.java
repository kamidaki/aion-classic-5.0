package com.aionemu.gameserver.model.stats.container;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.ai.AILogger;
import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.SummonedObject;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.templates.stats.NpcStatsTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.S_ACTION;
import com.aionemu.gameserver.taskmanager.tasks.PacketBroadcaster.BroadcastMode;
import com.aionemu.gameserver.utils.PacketSendUtility;


public class NpcGameStats extends CreatureGameStats<Npc> {

	int currentRunSpeed = 0;
	private long lastAttackTime = 0;
	private long lastAttackedTime = 0;
	private long nextAttackTime = 0;
	private long lastSkillTime = 0;
	private long fightStartingTime = 0;
	private int cachedState;
	private Stat cachedSpeedStat;
	private long lastGeoZUpdate;
	private long lastChangeTarget = 0;
        
	public NpcGameStats(Npc owner) {
		super(owner);
	}

	@Override
	protected void onStatsChange() {
		checkSpeedStats();
	}
	
	private void checkSpeedStats() {
		Stat oldSpeed = cachedSpeedStat;
		cachedSpeedStat = null;
		Stat newSpeed = getMovementSpeed();
		cachedSpeedStat = newSpeed;
		if (oldSpeed == null || oldSpeed.getCurrent() != newSpeed.getCurrent()) {
			owner.addPacketBroadcastMask(BroadcastMode.UPDATE_SPEED);
		}
	}

	@Override
	public Stat getMaxHp() {
		return getStat(StatEnum.MAXHP, owner.getObjectTemplate().getStatsTemplate().getMaxHp());
	}
	@Override
	public Stat getMaxMp() {
		return getStat(StatEnum.MAXMP, owner.getObjectTemplate().getStatsTemplate().getMaxHp());
	}
	@Override
	public Stat getAttackSpeed() {
		return getStat(StatEnum.ATTACK_SPEED, owner.getObjectTemplate().getAttackDelay());
	}
	public Stat getStrikeResist() {
		return getStat(StatEnum.PHYSICAL_CRITICAL_RESIST, 0);
	}
	public Stat getStrikeFort() {
        return getStat(StatEnum.PHYSICAL_CRITICAL_DAMAGE_REDUCE, 0);
    }
	public Stat getSpellResist() {
		return getStat(StatEnum.MAGICAL_CRITICAL_RESIST, 0);
	}
    public Stat getSpellFort() {
        return getStat(StatEnum.MAGICAL_CRITICAL_DAMAGE_REDUCE, 0);
    }
    public Stat getBCastingTime() {
        return getStat(StatEnum.BOOST_CASTING_TIME, 1000);
    }
	public Stat getConcentration() {
        return getStat(StatEnum.CONCENTRATION, ((Npc)this.owner).getObjectTemplate().getStatsTemplate().getConcentration());
    }
	public Stat getRootResistance() {
        return getStat(StatEnum.ROOT_RESISTANCE, 0);
    }
	public Stat getSnareResistance() {
        return getStat(StatEnum.SNARE_RESISTANCE, 0);
    }
	public Stat getBindResistance() {
        return getStat(StatEnum.BIND_RESISTANCE, 0);
    }
	public Stat getFearResistance() {
        return getStat(StatEnum.FEAR_RESISTANCE, 0);
    }
	public Stat getSleepResistance() {
        return getStat(StatEnum.SLEEP_RESISTANCE, 0);
    }
	@Override
	public Stat getMainHandMAccuracy() {
		if (owner instanceof SummonedObject) {
			return getStat(StatEnum.MAGICAL_ACCURACY, owner.getObjectTemplate().getStatsTemplate().getMagicalHitAccuracy());
		}
		return getMainHandPAccuracy();
	}
	public Stat getAllSpeed() {
		return getStat(StatEnum.ALLSPEED, 7500);
	}
	public Stat getPhysicalCriticalReduceRate() {
		return getStat(StatEnum.PHYSICAL_CRITICAL_REDUCE_RATE, ((Npc)this.owner).getObjectTemplate().getStatsTemplate().getPhysicalCriticalReduceRate());
	}
	public Stat getMagicalCriticalReduceRate() {
		return getStat(StatEnum.MAGICAL_CRITICAL_REDUCE_RATE, ((Npc)this.owner).getObjectTemplate().getStatsTemplate().getMagicalCriticalReduceRate());
	}
	public Stat getPhysicalCriticalDamageReduce() {
		return getStat(StatEnum.PHYSICAL_CRITICAL_DAMAGE_REDUCE, ((Npc)this.owner).getObjectTemplate().getStatsTemplate().getPhysicalCriticalDamageReduce());
	}
	public Stat getMagicalCriticalDamageReduce() {
		return getStat(StatEnum.MAGICAL_CRITICAL_DAMAGE_REDUCE, ((Npc)this.owner).getObjectTemplate().getStatsTemplate().getMagicalCriticalDamageReduce());
	}

	@Override
	public Stat getMovementSpeed() {
		int currentState = owner.getState();
		Stat cachedSpeed = cachedSpeedStat;
		if (cachedSpeed != null && cachedState == currentState) {
			return cachedSpeed;
		}
		Stat newSpeedStat = null;
		if (owner.isFlying()) {
			newSpeedStat = getStat(StatEnum.FLY_SPEED, Math.round(owner.getObjectTemplate().getStatsTemplate().getRunSpeed() * 1.3f * 1000.0f));
		} else if (owner.isInState(CreatureState.WEAPON_EQUIPPED)) {
			newSpeedStat = getStat(StatEnum.SPEED, Math.round(owner.getObjectTemplate().getStatsTemplate().getRunSpeedFight() * 1000.0f));
		} else if (owner.isInState(CreatureState.WALKING)) {
			newSpeedStat = getStat(StatEnum.SPEED, Math.round(owner.getObjectTemplate().getStatsTemplate().getWalkSpeed() * 1000.0f));
		} else {
			newSpeedStat = getStat(StatEnum.SPEED, Math.round(owner.getObjectTemplate().getStatsTemplate().getRunSpeed() * 1000.0f));
		}
		cachedState = currentState;
		cachedSpeedStat = newSpeedStat;
		return newSpeedStat;
	}

	@Override
	public Stat getAttackRange() {
		return getStat(StatEnum.ATTACK_RANGE, owner.getObjectTemplate().getAttackRange() * 1500);
	}

	@Override
	public Stat getPDef() {
		return getStat(StatEnum.PHYSICAL_DEFENSE, owner.getObjectTemplate().getStatsTemplate().getPhysicalDefend());
	}

	@Override
	public Stat getMDef() {
		return getStat(StatEnum.MAGICAL_DEFEND, 0);
	}

	@Override
	public Stat getMResist() {
		return getStat(StatEnum.MAGICAL_RESIST, owner.getObjectTemplate().getStatsTemplate().getMagicalResist());
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
		return getStat(StatEnum.ACCURACY, 100);
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
		return getStat(StatEnum.EVASION, owner.getObjectTemplate().getStatsTemplate().getEvasion());
	}

	@Override
	public Stat getParry() {
		return getStat(StatEnum.PARRY, owner.getObjectTemplate().getStatsTemplate().getParry());
	}

	@Override
	public Stat getBlock() {
		return getStat(StatEnum.BLOCK, owner.getObjectTemplate().getStatsTemplate().getBlock());
	}

	@Override
	public Stat getMainHandPAttack() {
		return getStat(StatEnum.PHYSICAL_ATTACK, owner.getObjectTemplate().getStatsTemplate().getPhysicalAttack());
	}

	@Override
	public Stat getMainHandPCritical() {
		return getStat(StatEnum.PHYSICAL_CRITICAL, owner.getObjectTemplate().getStatsTemplate().getCritical());
	}

	@Override
	public Stat getMainHandPAccuracy() {
		return getStat(StatEnum.PHYSICAL_ACCURACY, owner.getObjectTemplate().getStatsTemplate().getHitAccuracy());
	}

	@Override
	public Stat getMAttack() {
		return getStat(StatEnum.MAGICAL_ATTACK, owner.getObjectTemplate().getStatsTemplate().getMagicalAttack());
	}

	@Override
	public Stat getMainHandMAttack() {
		return getStat(StatEnum.MAGICAL_ATTACK, owner.getObjectTemplate().getStatsTemplate().getMagicalAttack());
	}

	@Override
	public Stat getOffHandMAttack() {
		return getStat(StatEnum.MAGICAL_ATTACK, 0);
	}

	@Override
	public Stat getMBoost() {
		return getStat(StatEnum.BOOST_MAGICAL_SKILL, 100);
	}

	@Override
	public Stat getMAccuracy() {
		if (owner instanceof SummonedObject) {
			return getStat(StatEnum.MAGICAL_ACCURACY, owner.getObjectTemplate().getStatsTemplate().getMagicalHitAccuracy());
		}
		return getMainHandPAccuracy();
	}

	@Override
	public Stat getMCritical() {
		return getStat(StatEnum.MAGICAL_CRITICAL, owner.getObjectTemplate().getStatsTemplate().getMagicalCritical());
	}

	@Override
	public Stat getHpRegenRate() {
		NpcStatsTemplate nst = owner.getObjectTemplate().getStatsTemplate();
		return getStat(StatEnum.REGEN_HP, nst.getHpRegen());
	}

	@Override
	public Stat getMpRegenRate() {
		throw new IllegalStateException("No mp regen for NPC");
	}

	public int getLastAttackTimeDelta() {
		return Math.round((System.currentTimeMillis() - lastAttackTime) / 1000f);
	}

	public int getLastAttackedTimeDelta() {
		return Math.round((System.currentTimeMillis() - lastAttackedTime) / 1000f);
	}

	public void renewLastAttackTime() {
		this.lastAttackTime = System.currentTimeMillis();
	}

	public void renewLastAttackedTime() {
		this.lastAttackedTime = System.currentTimeMillis();
	}

	public boolean isNextAttackScheduled() {
		return nextAttackTime - System.currentTimeMillis() > 50;
	}

    public void setFightStartingTime() {
        this.fightStartingTime = System.currentTimeMillis();
    }

    public long getFightStartingTime() {
        return this.fightStartingTime;
    }

	public void setNextAttackTime(long nextAttackTime) {
		this.nextAttackTime = nextAttackTime;
	}

	public int getNextAttackInterval() {
		long attackDelay = System.currentTimeMillis() - lastAttackTime;
		int attackSpeed = getAttackSpeed().getCurrent();
		if (attackSpeed == 0) {
			attackSpeed = 2000;
		} if (owner.getAi().isLogging()) {
			AILogger.info(owner.getAi(), "adelay = " + attackDelay + " aspeed = " + attackSpeed);
		}
		int nextAttack = 0;
		if (attackDelay < attackSpeed) {
			nextAttack = (int) (attackSpeed - attackDelay);
		}
		return nextAttack;
	}

	public void renewLastSkillTime() {
		this.lastSkillTime = System.currentTimeMillis();
	}

	public void renewLastChangeTargetTime() {
		this.lastChangeTarget = System.currentTimeMillis();
	}

	public int getLastSkillTimeDelta() {
		return Math.round((System.currentTimeMillis() - lastSkillTime) / 1000f);
	}

	public int getLastChangeTargetTimeDelta() {
		return Math.round((System.currentTimeMillis() - lastChangeTarget) / 1000f);
	}

	public boolean canUseNextSkill() {
		return this.getLastSkillTimeDelta() >= 6 + Rnd.get((int)-3, (int)3);
	}

	@Override
	public void updateSpeedInfo() {
		PacketSendUtility.broadcastPacket(owner, new S_ACTION(owner, EmotionType.START_EMOTE2, 0, 0));
	}

	public final long getLastGeoZUpdate() {
		return lastGeoZUpdate;
	}

	public void setLastGeoZUpdate(long lastGeoZUpdate) {
		this.lastGeoZUpdate = lastGeoZUpdate;
	}
}