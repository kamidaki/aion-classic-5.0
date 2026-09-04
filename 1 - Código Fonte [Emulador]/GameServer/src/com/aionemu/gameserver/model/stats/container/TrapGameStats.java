package com.aionemu.gameserver.model.stats.container;

import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.stats.container.NpcGameStats;
import com.aionemu.gameserver.model.stats.container.StatEnum;

public class TrapGameStats extends NpcGameStats
{
	public TrapGameStats(Npc owner) {
		super(owner);
	}
	
	@Override
    public Stat getStat(StatEnum statEnum, int base) {
        Stat stat = super.getStat(statEnum, base);
        if (((Npc)this.owner).getMaster() == null) {
            return stat;
        } switch (statEnum) {
            case BOOST_MAGICAL_SKILL: 
            case MAGICAL_ACCURACY: {
                stat.setBonusRate(0.7f);
                return ((Npc)this.owner).getMaster().getGameStats().getItemStatBoost(statEnum, stat);
            }
        }
        return stat;
    }
	
	@Override
    public Stat getAttackRange() {
        return this.getStat(StatEnum.ATTACK_RANGE, 7000);
    }
	
    public int getEffectiveRange() {
        int range = 10;
        return range;
    }
	
	@Override
    public Stat getMAccuracy() {
        int value = 2500;
        value = (int)((float)value * 1.2f);
        return this.getStat(StatEnum.MAGICAL_ACCURACY, value);
    }
}