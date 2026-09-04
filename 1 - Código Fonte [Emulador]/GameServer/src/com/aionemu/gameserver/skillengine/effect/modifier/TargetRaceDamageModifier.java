package com.aionemu.gameserver.skillengine.effect.modifier;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.effect.modifier.ActionModifier;
import com.aionemu.gameserver.skillengine.model.Effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "TargetRaceDamageModifier")
public class TargetRaceDamageModifier extends ActionModifier
{
	@XmlAttribute(name = "race")
	private Race skillTargetRace;

	@Override
    public int analyze(Effect effect) {
        Npc npc;
        Creature effected = effect.getEffected();
        int newValue = this.value + effect.getSkillLevel() * this.delta;
        if (effected instanceof Player player) {            switch (this.skillTargetRace) {
                case ASMODIANS: {
                    if (player.getRace() == Race.ASMODIANS) {
                        return newValue;
                    }
                } case ELYOS: {
                    if (player.getRace() == Race.ELYOS) {
						return newValue;
					}
                }
            }
        } else if (effected instanceof Npc && (npc = (Npc)effected).getObjectTemplate().getRace().toString().equals(this.skillTargetRace.toString())) {
            return newValue;
        }
        return 0;
    }

    @Override
    public boolean check(Effect effect) {
        Creature effected = effect.getEffected();
        if (effected instanceof Player player) {            switch (this.skillTargetRace) {
                case ASMODIANS: {
                    if (player.getRace() == Race.ASMODIANS) {
                        return true;
                    }
                } case ELYOS: {
                    if (player.getRace() == Race.ELYOS) {
                        return true;
                    }
                }
            }
        } else if (effected instanceof Npc npc) {            Race race = npc.getObjectTemplate().getRace();
            if (race == null) {
                return false;
            }
            return race.toString().equals(this.skillTargetRace.toString());
        }
        return false;
    }
}