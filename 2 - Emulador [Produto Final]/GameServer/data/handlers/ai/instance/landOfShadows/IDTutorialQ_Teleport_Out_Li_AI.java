package ai.instance.landOfShadows;

import static com.aionemu.gameserver.model.DialogAction.TELEPORT_SIMPLE;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.handler.TalkEventHandler;
import com.aionemu.gameserver.model.animations.TeleportAnimation;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DIALOG_WINDOW;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.PacketSendUtility;

import ai.GeneralNpcAI;

/**
 * AI para Inggril (804134, Daeva do Tempo, Elyos) na Land of Shadows (390000000).
 * Responde com página de diálogo 1011 e, na ação 104 (TELEPORT_SIMPLE),
 * teletransporta o jogador para Sanctum (110010000).
 */
@AIName("idtutorialq_teleport_out_li")
public class IDTutorialQ_Teleport_Out_Li_AI extends GeneralNpcAI {

	public IDTutorialQ_Teleport_Out_Li_AI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleDialogStart(Player player) {
		TalkEventHandler.onSimpleTalk((NpcAI) getOwner().getAi(), player);
		PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getOwner().getObjectId(), 1011));
	}

	@Override
	public boolean onDialogSelect(Player player, int dialogActionId, int questId, int extendedRewardIndex) {
		if (dialogActionId == TELEPORT_SIMPLE) {
			PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 0));
			TeleportService.teleportTo(player, 110010000, 1313.25f, 1512.011f, 568.107f, (byte) 58, TeleportAnimation.FADE_OUT_BEAM);
			return true;
		}
		return super.onDialogSelect(player, dialogActionId, questId, extendedRewardIndex);
	}
}
