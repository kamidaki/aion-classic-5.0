package com.aionemu.gameserver.skillengine.action;

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
@XmlType(name = "SpUseAction")
public class SpUseAction extends Action {

	@XmlAttribute(required = true)
	protected int value;

	public int getValue() {
		return value;
	}

	@Override
	public boolean act(Skill skill) {
		if (!canAct(skill))
			return false;
		// 5.0 oficial: MO_Elec_G2 e TH_MoveShadow_G1 tiram 10 de SP uma vez, e o valor novo sai no 0x14B do tick seguinte
		if (skill.getEffector() instanceof Player player)
			player.getLifeStats().reduceSp(value);
		return true;
	}

	@Override
	public boolean canAct(Skill skill) {
		if (skill.getEffector() instanceof Player player && player.getLifeStats().getCurrentSp() < value) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_SKILL_NOT_ENOUGH_SP());
			return false;
		}
		return true;
	}
}
