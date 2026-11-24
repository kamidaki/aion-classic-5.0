package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.mail.BlackCloudMailService;

/**
 * [C_SA_CONFIRMGOODS] (0x9E, 8 b): {@code [Q id da mercadoria]}, um por mercadoria, inclusive no "Receber tudo".
 */
public class CM_NPSHOP_GOODS_RECV extends AionClientPacket {

	private long goodsId;

	public CM_NPSHOP_GOODS_RECV(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		goodsId = readQ();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			BlackCloudMailService.receiveGoods(player, goodsId);
	}
}
