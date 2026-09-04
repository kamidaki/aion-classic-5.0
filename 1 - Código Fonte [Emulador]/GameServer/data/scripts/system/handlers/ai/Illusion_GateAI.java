package ai;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.AIRequest;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.S_ASK;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.PacketSendUtility;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Illusion_Gate")
public class Illusion_GateAI extends NpcAI
{
	@Override
	protected void handleDialogStart(Player player) {
		boolean isMember = false;
		int creatorId = getCreatorId();
		if (player.getObjectId().equals(creatorId)) {
			isMember = true;
		} else if (player.isInGroup()) {
			isMember = player.getPlayerGroup().hasMember(creatorId);
		} if (isMember && player.getLevel() >= 10) {
			AIActions.addRequest(this, player, S_ASK.STR_ASK_GROUP_GATE_DO_YOU_ACCEPT_MOVE, 0, 9, new AIRequest() {
				private boolean decided = false;
				@Override
				public void acceptRequest(Creature requester, Player responder) {
					if (!decided) {
						switch (getNpcId()) {
							case 749017:
								TeleportService.teleportTo(responder, 110010000, 1444.0000f, 1577.0000f, 572.0000f, (byte) 0);
							break;
							case 749083:
								TeleportService.teleportTo(responder, 120010000, 1657.0000f, 1398.0000f, 194.0000f, (byte) 0);
							break;
						}
						decided = true;
					}
				}
				@Override
				public void denyRequest(Creature requester, Player responder) {
					decided = true;
				}
			});
		} else {
			PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_SKILL_CAN_NOT_USE_GROUPGATE_NO_RIGHT);
		}
	}
}