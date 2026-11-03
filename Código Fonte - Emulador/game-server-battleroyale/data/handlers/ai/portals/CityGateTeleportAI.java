package ai.portals;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.DialogAction;
import com.aionemu.gameserver.model.animations.TeleportAnimation;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DIALOG_WINDOW;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.PacketSendUtility;

import ai.GeneralNpcAI;

/**
 * AI for Gatekeeper NPCs at capital entrance maps:
 * - 730648 (Sanctum Gate 110030000 -> Sanctum 110010000)
 * - 730649 (Pandaemonium Entrance 120030000 -> Pandaemonium 120010000)
 *
 * Opens conversation dialogue on interaction and teleports the player into the city
 * when confirmed via dialogue action, preventing immediate unwanted teleportation.
 */
@AIName("city_gate_teleport")
public class CityGateTeleportAI extends GeneralNpcAI {

	public CityGateTeleportAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleDialogStart(Player player) {
		super.handleDialogStart(player);
	}

	@Override
	public boolean onDialogSelect(Player player, int dialogActionId, int questId, int extendedRewardIndex) {
		if (QuestEngine.getInstance().onDialog(new QuestEnv(getOwner(), player, questId, dialogActionId))) {
			return true;
		}

		if (dialogActionId == DialogAction.NULL || dialogActionId == 0) {
			PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 0));
			return true;
		}

		if (getNpcId() == 730648) {
			// Sanctum Gate (110030000) -> Sanctum (110010000)
			PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 0));
			TeleportService.teleportTo(player, 110010000, 1313.25f, 1512.011f, 568.107f, (byte) 58, TeleportAnimation.FADE_OUT_BEAM);
			return true;
		} else if (getNpcId() == 730649) {
			// Pandaemonium Entrance (120030000) -> Pandaemonium (120010000)
			PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 0));
			TeleportService.teleportTo(player, 120010000, 1657.5f, 1398.7f, 194.7f, (byte) 0, TeleportAnimation.FADE_OUT_BEAM);
			return true;
		}

		return super.onDialogSelect(player, dialogActionId, questId, extendedRewardIndex);
	}
}
