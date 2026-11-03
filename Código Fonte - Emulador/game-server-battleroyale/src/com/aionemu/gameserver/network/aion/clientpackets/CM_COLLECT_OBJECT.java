package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Decodificado 0x131 (cru 0x1C3): clique num objeto de coleta com barra própria (ui_type craft_ui_always no client_npcs), [D objeto].
 * <p>
 * 5.0 oficial (Balic Treasury.pcapng, 29/10): o cliente manda este pacote no lugar do C_DIALOG ao clicar no 802959 Blood Drana Products, e o
 * servidor responde com o S 0x195 ({@link com.aionemu.gameserver.network.aion.serverpackets.SM_COLLECT_OBJECT_PROGRESS}). Quem cuida da coleta é
 * a AI do objeto, pelo mesmo caminho do diálogo (alcance de conversa e evento DIALOG_START).
 */
public class CM_COLLECT_OBJECT extends AionClientPacket {

	private int targetObjectId;

	public CM_COLLECT_OBJECT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		targetObjectId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null || player.isTrading())
			return;
		if (player.getKnownList().getObject(targetObjectId) instanceof Npc target)
			target.getController().onDialogRequest(player);
	}
}
