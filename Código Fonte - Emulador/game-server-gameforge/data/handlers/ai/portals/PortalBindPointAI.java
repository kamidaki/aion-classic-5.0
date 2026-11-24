package ai.portals;

import static com.aionemu.gameserver.model.DialogAction.SETPRO1;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DIALOG_WINDOW;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.PacketSendUtility;

import ai.GeneralNpcAI;

/**
 * Portal que leva ao ponto registrado (obelisco) do jogador.
 * <p>
 * 801995 (LDF4b_Combine_LF4_Teleport_01, saída Elyos de Tiamaranta): o diálogo do cliente diz "Teleport to the registered Obelisk"
 * (HACTION_SETPRO1). Captura oficial de 21/10: clique -> página 1011, ação 10000 -> o jogador volta ao bind point (Inggison 1383.59,
 * 307.36, 588.87, o mesmo ponto do Return).
 */
@AIName("portal_bind_point")
public class PortalBindPointAI extends GeneralNpcAI {

	public PortalBindPointAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleDialogStart(Player player) {
		PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 1011));
	}

	@Override
	public boolean onDialogSelect(Player player, int dialogActionId, int questId, int extendedRewardIndex) {
		if (dialogActionId == SETPRO1) {
			PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 0));
			TeleportService.moveToBindLocation(player);
		}
		return true;
	}
}
