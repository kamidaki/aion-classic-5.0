package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_MYLIST, decodificado 0x115 (cru 0x1EF): [D moeda]. Mandado ao escolher kinah (1) ou Luna (0) na aba de registro, antes
 * do C_GLOBAL_TRADE_AVG_PRICE (2 de 2 na captura), e respondido pelo S_GLOBAL_TRADE_MYLIST (0x13D).
 */
public class CM_GLOBAL_TRADE_MYLIST extends AionClientPacket {

	private int currency = -1;

	public CM_GLOBAL_TRADE_MYLIST(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		currency = getRemainingBytes() == 4 ? readD() : -1;
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			GlobalTradeService.getInstance().sendMyList(player, GlobalTradeCurrency.of(currency));
	}
}
