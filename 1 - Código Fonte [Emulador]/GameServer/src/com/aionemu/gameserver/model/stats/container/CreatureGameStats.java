package com.aionemu.gameserver.model.stats.container;

import com.aionemu.gameserver.model.SkillElement;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.stats.calc.*;
import com.aionemu.gameserver.model.stats.calc.functions.IStatFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunctionProxy;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.TreeSet;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public abstract class CreatureGameStats<T extends Creature>
{
    protected static final Logger log = LoggerFactory.getLogger(CreatureGameStats.class);
    private static final int ATTACK_MAX_COUNTER = Integer.MAX_VALUE;
    private long lastGeoUpdate = 0;
    private Map<StatEnum, TreeSet<IStatFunction>> stats;
    private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();
    private int attackCounter = 0;
    protected T owner = null;
    private Stat cachedHPStat;
    private Stat cachedMPStat;

    protected CreatureGameStats(T owner) {
        this.owner = owner;
        this.stats = new ConcurrentHashMap<StatEnum, TreeSet<IStatFunction>>();
    }

    /**
     * @return the atcount
     */
    public int getAttackCounter() {
        return attackCounter;
    }

    /**
     * @param atcount the atcount to set
     */
    protected void setAttackCounter(int attackCounter) {
        if (attackCounter <= 0) {
            this.attackCounter = 1;
        } else {
            this.attackCounter = attackCounter;
        }
    }

    public void increaseAttackCounter() {
        if (attackCounter == ATTACK_MAX_COUNTER) {
            this.attackCounter = 1;
        } else {
            this.attackCounter++;
        }
    }

    public final void addEffectOnly(StatOwner statOwner, List<? extends IStatFunction> functions) {
        lock.writeLock().lock();
        try {
            for (IStatFunction function : functions) {
                if (!stats.containsKey(function.getName())) {
                    stats.put(function.getName(), new TreeSet<IStatFunction>());
                }
                IStatFunction func = function;
                if (function instanceof StatFunction) {
                    func = new StatFunctionProxy(statOwner, function);
                }
                addFunction(function.getName(), func);
            }
        } finally {
            lock.writeLock().unlock();
        }
    }

    public final void addEffect(StatOwner statOwner, List<? extends IStatFunction> functions) {
        addEffectOnly(statOwner, functions);
        onStatsChange();
    }

    public final void endEffect(StatOwner statOwner) {
        lock.writeLock().lock();
        try {
            for (TreeSet<IStatFunction> value : stats.values()) {
                for (Iterator<IStatFunction> iter = value.iterator(); iter.hasNext(); ) {
                    IStatFunction ownedMod = iter.next();
                    if (ownedMod.getOwner() != null && ownedMod.getOwner().equals(statOwner)) {
                        iter.remove();
                    }
                }
            }
        } finally {
            lock.writeLock().unlock();
        }
        onStatsChange();
    }

    public int getPositiveStat(StatEnum statEnum, int base) {
        Stat stat = getStat(statEnum, base);
        int value = stat.getCurrent();
        return value > 0 ? value : 0;
    }

    public int getPositiveReverseStat(StatEnum statEnum, int base) {
        Stat stat = getReverseStat(statEnum, base);
        int value = stat.getCurrent();
        return value > 0 ? value : 0;
    }

    public Stat getStat(StatEnum statEnum, int base) {
        Stat stat = new AdditionStat(statEnum, base, (Creature) owner);
        return getStat(statEnum, stat);
    }

    public Stat getStat(StatEnum statEnum, int base, float bonusRate) {
        Stat stat = new AdditionStat(statEnum, base, (Creature) owner, bonusRate);
        return getStat(statEnum, stat);
    }

    public Stat getReverseStat(StatEnum statEnum, int base) {
        Stat stat = new ReverseStat(statEnum, base, (Creature) owner);
        return getStat(statEnum, stat);
    }

    public Stat getReverseStat(StatEnum statEnum, int base, float bonusRate) {
        Stat stat = new ReverseStat(statEnum, base, (Creature) owner, bonusRate);
        return getStat(statEnum, stat);
    }

    public Stat getStat(StatEnum statEnum, Stat stat) {
        lock.readLock().lock();
        try {
            TreeSet<IStatFunction> functions = getStatsByStatEnum(statEnum);
            if (functions == null) {
                return stat;
            }
            for (IStatFunction func : functions) {
                if (func.validate(stat, func)) {
                    func.apply(stat);
                }
            }
            StatCapUtil.calculateBaseValue(stat, ((Creature) owner).isPlayer());
            return stat;
        } finally {
            lock.readLock().unlock();
        }
    }

    public Stat getItemStatBoost(StatEnum statEnum, Stat stat) {
        lock.readLock().lock();
        try {
            TreeSet<IStatFunction> functions = getStatsByStatEnum(statEnum);
            if (functions == null || functions.isEmpty()) {
                return stat;
            }
            for (IStatFunction func : functions) {
                if (func.validate(stat, func) && (func.getOwner() instanceof Item || func.getOwner() instanceof ManaStone)) {
                    func.apply(stat);
                }
            }
        } finally {
            lock.readLock().unlock();
        }
        return stat;
    }

    public abstract Stat getMaxHp();

    public abstract Stat getMaxMp();

    public abstract Stat getAttackSpeed();

    public abstract Stat getMovementSpeed();

    public abstract Stat getAttackRange();

    public abstract Stat getPDef();

    public abstract Stat getMDef();

    public abstract Stat getMResist();

    public abstract Stat getPower();

    public abstract Stat getHealth();

    public abstract Stat getAccuracy();

    public abstract Stat getAgility();

    public abstract Stat getKnowledge();

    public abstract Stat getWill();

    public abstract Stat getEvasion();

    public abstract Stat getParry();

    public abstract Stat getBlock();

    public abstract Stat getMainHandPAttack();

    public abstract Stat getMainHandPCritical();

    public abstract Stat getMainHandPAccuracy();
	
	public abstract Stat getMAttack();

    public abstract Stat getMainHandMAttack();

    public abstract Stat getOffHandMAttack();

    public abstract Stat getMBoost();

    public abstract Stat getMBResist();

    public abstract Stat getMAccuracy();

    public abstract Stat getMCritical();

    public abstract Stat getHpRegenRate();

    public abstract Stat getMpRegenRate();

	public abstract Stat getStrikeResist();

	public abstract Stat getStrikeFort();

	public abstract Stat getSpellResist();

	public abstract Stat getSpellFort();

	public abstract Stat getBCastingTime();

	public abstract Stat getConcentration();

	public abstract Stat getRootResistance();

	public abstract Stat getSnareResistance();

	public abstract Stat getBindResistance();

	public abstract Stat getFearResistance();

    public abstract Stat getSleepResistance();

    public abstract Stat getMainHandMAccuracy();

    public abstract Stat getAllSpeed();

    public int getMagicalDefenseFor(SkillElement element) {
        switch (element) {
            case EARTH:
                return getStat(StatEnum.EARTH_RESISTANCE, 0).getCurrent();
            case FIRE:
                return getStat(StatEnum.FIRE_RESISTANCE, 0).getCurrent();
            case WATER:
                return getStat(StatEnum.WATER_RESISTANCE, 0).getCurrent();
            case WIND:
                return getStat(StatEnum.WIND_RESISTANCE, 0).getCurrent();
            case LIGHT:
                return getStat(StatEnum.ELEMENTAL_RESISTANCE_LIGHT, 0).getCurrent();
            case DARK:
                return getStat(StatEnum.ELEMENTAL_RESISTANCE_DARK, 0).getCurrent();
            default:
                return 0;
        }
    }

    public float getMovementSpeedFloat() {
        return getMovementSpeed().getCurrent() / 1000f;
    }

    /**
     * Send packet about stats info
     */
    public void updateStatInfo() {
    }

    /**
     * Send packet about speed info
     */
    public void updateSpeedInfo() {
    }

    public TreeSet<IStatFunction> getStatsByStatEnum(StatEnum stat) {
        TreeSet<IStatFunction> allStats = stats.get(stat);
        if (allStats == null) {
            return null;
        }
        TreeSet<IStatFunction> tmp = new TreeSet<IStatFunction>();
        List<IStatFunction> setFuncs = null;
        for (IStatFunction func : allStats) {
            if (func.getPriority() >= Integer.MAX_VALUE - 10) {
                if (setFuncs == null) {
                    setFuncs = new ArrayList<IStatFunction>();
                }
                setFuncs.add(func);
            } else if (setFuncs != null) {
                break;
            }
        } if (setFuncs == null) {
            tmp.addAll(allStats);
        } else {
            tmp.addAll(setFuncs);
        }
        return tmp;
    }

    private void addFunction(StatEnum stat, IStatFunction function) {
        TreeSet<IStatFunction> allStats = stats.get(stat);
        allStats.add(function);
    }

    /**
     * @return
     */
    public boolean checkGeoNeedUpdate() {
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastGeoUpdate > 600) {
            lastGeoUpdate = currentTime;
            return true;
        }
        return false;
    }

    /**
     * Perform additional calculations after effects added/removed<br>
     * This method will be called outside of stats lock.
     */
    protected void onStatsChange() {
        checkHPStats();
        checkMPStats();
    }
	
    private void checkHPStats() {
        Stat oldHP = cachedHPStat;
        cachedHPStat = null;
        Stat newHP = this.getMaxHp();
        cachedHPStat = newHP;
        if (oldHP == null) {
            return;
        } if (oldHP.getCurrent() != newHP.getCurrent()) {
            float percent = 1f * newHP.getCurrent() / oldHP.getCurrent();
            owner.getLifeStats().setCurrentHp(Math.round(owner.getLifeStats().getCurrentHp() * percent));
        }
    }
	
    private void checkMPStats() {
        Stat oldMP = cachedMPStat;
        cachedMPStat = null;
        Stat newMP = this.getMaxMp();
        cachedMPStat = newMP;
        if (oldMP == null) {
            return;
        } if (oldMP.getCurrent() != newMP.getCurrent()) {
            float percent = 1f * newMP.getCurrent() / oldMP.getCurrent();
            owner.getLifeStats().setCurrentMp(Math.round(owner.getLifeStats().getCurrentMp() * percent));
        }
    }
}