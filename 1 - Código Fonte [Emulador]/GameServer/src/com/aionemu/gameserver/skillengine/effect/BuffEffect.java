package com.aionemu.gameserver.skillengine.effect;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.stats.calc.functions.IStatFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatAddFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatRateFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatSetFunction;
import com.aionemu.gameserver.model.stats.container.CreatureGameStats;
import com.aionemu.gameserver.network.aion.serverpackets.S_HIT_POINT_OTHER.TYPE;
import com.aionemu.gameserver.skillengine.change.Change;
import com.aionemu.gameserver.skillengine.condition.Conditions;
import com.aionemu.gameserver.skillengine.model.Effect;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BuffEffect")
public abstract class BuffEffect extends EffectTemplate
{
	@XmlAttribute
    protected boolean maxstat;
	
	@Override
    public void applyEffect(Effect effect) {
        effect.addToEffectedController();
    }
	
    @Override
    public void endEffect(Effect effect) {
        Creature effected = effect.getEffected();
        effected.getGameStats().endEffect(effect);
    }
	
    @Override
    public void startEffect(Effect effect) {
		if (change == null) {
			return;
		}
        Creature effected = effect.getEffected();
        CreatureGameStats<? extends Creature> cgs = effected.getGameStats();
        List<IStatFunction> modifiers = this.getModifiers(effect);
        if (modifiers.size() > 0) {
            cgs.addEffect(effect, modifiers);
        } if (this.maxstat) {
            effected.getLifeStats().increaseHp(TYPE.HP, effected.getGameStats().getMaxHp().getCurrent());
			effected.getLifeStats().increaseMp(TYPE.HEAL_MP, effected.getGameStats().getMaxMp().getCurrent());
        }
    }
	
    protected List<IStatFunction> getModifiers(Effect effect) {
        int skillId = effect.getSkillId();
        int skillLvl = effect.getSkillLevel();
        List<IStatFunction> modifiers = new ArrayList<IStatFunction>();
        for (Change changeItem : change) {
            if (changeItem.getStat() == null) {
				log.warn("Skill stat has wrong name for skillid: " + skillId);
                continue;
            }
            int valueWithDelta = changeItem.getValue() + changeItem.getDelta() * skillLvl;
            Conditions conditions = changeItem.getConditions();
            switch (changeItem.getFunc()) {
                case ADD: {
                    modifiers.add(new StatAddFunction(changeItem.getStat(), valueWithDelta, true).withConditions(conditions));
                    break;
                } case PERCENT: {
                    modifiers.add(new StatRateFunction(changeItem.getStat(), valueWithDelta, true).withConditions(conditions));
                    break;
                } case REPLACE: {
                    modifiers.add(new StatSetFunction(changeItem.getStat(), valueWithDelta, true).withConditions(conditions));
                }
            }
        }
        return modifiers;
    }
	
    @Override
    public void onPeriodicAction(Effect effect) {
    }
}