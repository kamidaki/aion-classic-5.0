package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Botoes "Alterar aparencia" / "Alterar genero" do Aion Look. Dec 0x0113, fio 0x01E1, [C tipo]: 0 aparencia, 1 genero.
 * Captura oficial aionlook.pcapng (30/09): o oficial responde S_EDIT_CHARACTER [D obj][C 2][C tipo] e o cliente segue com C_ASK_QUIT [01],
 * como no NPC.
 */
public class CM_AIONLOOK_EDIT_CHARACTER extends AionClientPacket {

	private int type;

	public CM_AIONLOOK_EDIT_CHARACTER(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		type = readUC();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		CM_CHARACTER_EDIT.openEditScreen(player, type == 1, "Aion Look");
	}
}
