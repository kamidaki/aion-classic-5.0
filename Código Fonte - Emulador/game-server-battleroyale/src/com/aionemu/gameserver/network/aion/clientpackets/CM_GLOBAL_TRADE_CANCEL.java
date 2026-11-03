package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_CANCEL, decodificado 0x100 (cru 0x1F2): [Q anúncio] (2 de 2 na captura de 2026-09-21), respondido pelo
 * S_GLOBAL_TRADE_CANCEL (0x140).
 */
public class CM_GLOBAL_TRADE_CANCEL extends AionClientPacket {

	private long listingId;

	public CM_GLOBAL_TRADE_CANCEL(int opcode, Set<State> validStates) {
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
			GlobalTradeService.getInstance().cancel(player, listingId);
	}
}
