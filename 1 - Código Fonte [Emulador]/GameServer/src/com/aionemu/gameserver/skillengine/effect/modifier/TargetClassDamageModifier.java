package com.aionemu.gameserver.skillengine.effect.modifier;

import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.effect.modifier.ActionModifier;
import com.aionemu.gameserver.skillengine.model.Effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "TargetClassDamageModifier")
public class TargetClassDamageModifier extends ActionModifier
{
	@XmlAttribute(name = "class")
	private PlayerClass skillTargetClass;

	@Override
    public int analyze(Effect effect) {
        Player player;
        Creature effected = effect.getEffected();
        if (effected instanceof Player && (player = (Player)effected).getPlayerClass() == this.skillTargetClass) {
            return this.value + effect.getSkillLevel() * this.delta;
        }
        return 0;
    }

    @Override
    public boolean check(Effect effect) {
        Creature effected = effect.getEffected();
        if (effected instanceof Player player) {            return player.getPlayerClass() == this.skillTargetClass;
        }
        return false;
    }
}