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
@XmlType(name = "HpCondition")
public class HpCondition extends Condition {

	@XmlAttribute(required = true)
	protected int value;
	@XmlAttribute
	protected int delta;
	@XmlAttribute
	protected boolean ratio;

	@Override
	public boolean validate(Skill skill) {
		// só confere: quem cobra é o <hpuse> no fim do cast. Todo template com <hp> também tem <hpuse>, e cobrar aqui pagava o custo duas vezes
		// (5.0 oficial: um único -300 por ataque do servant, junto do resultado)
		return canValidate(skill);
	}

	@Override
	public boolean canValidate(Skill skill) {
		// npcs are never blocked by an hp cost, they pay what they have, see validate()
		if (skill.getEffector() instanceof Player player && player.getLifeStats().getCurrentHp() <= getCost(skill)) { // the cast may never be lethal
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_SKILL_NOT_ENOUGH_HP());
			return false;
		}
		return true;
	}

	private int getCost(Skill skill) {
		int valueWithDelta = value + delta * skill.getSkillLevel();
		if (ratio)
			valueWithDelta = (skill.getEffector().getLifeStats().getMaxHp() * valueWithDelta) / 100;
		return valueWithDelta;
	}

	public int getHpValue() {
		return value;
	}

}
