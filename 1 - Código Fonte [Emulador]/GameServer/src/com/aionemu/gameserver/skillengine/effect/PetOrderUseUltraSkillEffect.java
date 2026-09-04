package com.aionemu.gameserver.skillengine.effect;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.S_ALLOW_PET_USE_SKILL;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.PacketSendUtility;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "PetOrderUseUltraSkillEffect")
public class PetOrderUseUltraSkillEffect extends EffectTemplate
{
	@XmlAttribute
	protected boolean release;

	@Override
    public void applyEffect(Effect effect) {
        Player effector = (Player)effect.getEffector();
        if (effector.getSummon() == null) {
            return;
        }
        int effectorId = effector.getSummon().getObjectId();
        int npcId = effector.getSummon().getNpcId();
        int orderSkillId = effect.getSkillId();
        int petUseSkillId = DataManager.PET_SKILL_DATA.getPetOrderSkill(orderSkillId, npcId);
        int skillLvl = DataManager.SKILL_DATA.getSkillTemplate(petUseSkillId).getLvl();
        int targetId = effect.getEffected().getObjectId();
        effector.getSummon().addSkillOrder(petUseSkillId, skillLvl, this.release, effect.getEffected());
        PacketSendUtility.sendPacket(effector, new S_ALLOW_PET_USE_SKILL(effectorId, petUseSkillId, skillLvl, targetId));
    }
	
	@Override
    public void calculate(Effect effect) {
        if (effect.getEffector() instanceof Player && effect.getEffected() != null) {
            super.calculate(effect, null, null);
        }
    }
}