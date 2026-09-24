package com.aionemu.gameserver.skillengine.condition;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.skillengine.model.Skill;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SpCondition")
public class SpCondition extends Condition {

	@XmlAttribute(required = true)
	protected int value;

	public int getValue() {
		return value;
	}

	@Override
	public boolean validate(Skill skill) {
		// só confere: quem cobra é o <spuse> no fim do cast, como o <mp>/<mpuse>
		return canValidate(skill);
	}

	@Override
	public boolean canValidate(Skill skill) {
		if (skill.getEffector() instanceof Player player && player.getLifeStats().getCurrentSp() < value) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_SKILL_NOT_ENOUGH_SP());
			return false;
		}
		return true;
	}
}
