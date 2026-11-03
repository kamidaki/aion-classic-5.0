package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.item.ItemUpgradeService;

/**
 * C_START_ITEM_UPGRADE provável, decodificado 0x106 (cru 0x1FC): botão "Ascend" da janela aberta pelo quick menu, sem NPC.
 * <p>
 * Captura (1 de 1, 12 b): [D receita][D objeto][D opção], com a receita 1070 (uma opção só) e opção 0. As receitas de duas opções diferem só no
 * material, então o último D é o índice da opção escolhida.
 */
public class CM_ITEM_UPGRADE extends AionClientPacket {

	private int recipeId;
	private int itemObjectId;
	private int optionIndex;

	public CM_ITEM_UPGRADE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		recipeId = readD();
		itemObjectId = readD();
		optionIndex = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			ItemUpgradeService.start(player, recipeId, itemObjectId, optionIndex);
	}
}
