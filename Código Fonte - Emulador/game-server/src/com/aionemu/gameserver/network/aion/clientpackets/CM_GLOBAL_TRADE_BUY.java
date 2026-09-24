package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_BUY, decodificado 0x116 (cru 0x1EC): [Q anúncio] (2 de 2 capturas). Compra o anúncio inteiro.
 */
public class CM_GLOBAL_TRADE_BUY extends AionClientPacket {

	private long listingId;

	public CM_GLOBAL_TRADE_BUY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		listingId = readQ();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			GlobalTradeService.getInstance().buy(player, listingId);
	}
}
