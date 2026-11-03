package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * Decodificado 0x10C (cru 0x1E6), sem corpo: o cliente manda ao abrir a Global Auction House (4 de 4 capturas), respondido pelo
 * S_GLOBAL_TRADE_STATE (0x144).
 */
public class CM_GLOBAL_TRADE_STATE extends AionClientPacket {

	public CM_GLOBAL_TRADE_STATE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			GlobalTradeService.getInstance().sendState(player);
	}
}
