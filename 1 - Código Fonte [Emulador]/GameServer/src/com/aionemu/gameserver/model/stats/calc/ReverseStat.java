package com.aionemu.gameserver.model.stats.calc;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.container.StatEnum;

public class ReverseStat extends Stat
{
    public ReverseStat(StatEnum stat, int base, Creature owner) {
        super(stat, base, owner);
    }

    public ReverseStat(StatEnum stat, int base, Creature owner, float bonusRate) {
        super(stat, base, owner, bonusRate);
    }

    @Override
    public void addToBase(int base) {
        this.base -= base;
        if (this.base < 0) {
            this.base = 0;
        }
    }

    @Override
    public void addToBonus(int bonus) {
        this.bonus = (int)((float)this.bonus - this.bonusRate * (float)bonus);
    }

    @Override
    public float calculatePercent(int delta) {
        float percent = (float)(100 - delta) / 100.0f;
        return percent < 0.0f ? 0.0f : percent;
    }
}