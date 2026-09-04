package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.serverpackets.S_CHANGE_STANCE;
import com.aionemu.gameserver.skillengine.model.SkillTargetSlot;
import com.aionemu.gameserver.utils.PacketSendUtility;

public class CM_TOGGLE_SKILL_DEACTIVATE extends AionClientPacket
{
	private int skillId;
	
    public CM_TOGGLE_SKILL_DEACTIVATE(int opcode, AionConnection.State state, AionConnection.State ... restStates) {
        super(opcode, state, restStates);
    }
	
    protected void readImpl() {
        this.skillId = this.readH();
    }
	
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		
		SkillTargetSlot slot = DataManager.SKILL_DATA.getSkillTemplate(skillId).getTargetSlot();
		
		if (slot == SkillTargetSlot.BUFF) {
            player.getEffectController().removeEffect(skillId);
        } else if (slot == SkillTargetSlot.NOSHOW) {
            player.getEffectController().removeNoshowEffect(skillId);
        }
		
		if (player.getController().getStanceSkillId() == skillId) {
			PacketSendUtility.sendPacket(player, new S_CHANGE_STANCE(player, 0));
			player.getController().startStance(0);
		}
    }
}