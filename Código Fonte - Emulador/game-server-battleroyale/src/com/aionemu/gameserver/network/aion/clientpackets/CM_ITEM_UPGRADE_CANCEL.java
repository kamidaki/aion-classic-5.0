package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.item.ItemUpgradeService;

/**
 * C_CANCEL_ITEM_UPGRADE, decodificado 0x142 (cru 0x230): [D itemId do item na janela do Ascend].
 * <p>
 * Capturas: em Outros/outros_2026-09-21_14-43-57 (2 de 2) chega durante o Ascend da receita 1071 com o itemId de origem 123001182, e o oficial
 * interrompe com S 0x1AD [D 0][C 2][D 0], sem mensagem e sem gastar nada. Em Outros/outros_2026-09-21_06-10-28 (2 de 2) chega sem Ascend em
 * andamento, e o oficial não responde.
 */
public class CM_ITEM_UPGRADE_CANCEL extends AionClientPacket {

	private int itemId;

	public CM_ITEM_UPGRADE_CANCEL(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			ItemUpgradeService.cancel(player, itemId);
	}
}
