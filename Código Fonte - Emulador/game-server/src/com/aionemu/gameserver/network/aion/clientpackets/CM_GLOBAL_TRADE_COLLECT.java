package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_COLLECT, decodificado 0x102 (cru 0x1F0): [D moeda]. Na captura, [D 1] recebeu a venda em kinah (+184.000) e foi respondido
 * pelo S_GLOBAL_TRADE_COLLECT (0x142) e pelo histórico (0x145).
 */
public class CM_GLOBAL_TRADE_COLLECT extends AionClientPacket {

	private int currency = -1;

	public CM_GLOBAL_TRADE_COLLECT(int opcode, Set<State> validStates) {
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
			GlobalTradeService.getInstance().collect(player, GlobalTradeCurrency.of(currency));
	}
}
