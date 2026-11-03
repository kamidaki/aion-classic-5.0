package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_HISTORY, decodificado 0x10D (cru 0x1E7), 6 bytes como o C_GLOBAL_TRADE_SALESLOG: [C][C][C moeda][C][H]. Mandado ao abrir a
 * aba de histórico de receitas (3 na captura de 2026-09-21, moedas 0 e 1) e respondido pelo S_GLOBAL_TRADE_HISTORY (0x145).
 */
public class CM_GLOBAL_TRADE_HISTORY extends AionClientPacket {

	private int currency = -1;

	public CM_GLOBAL_TRADE_HISTORY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() == 6) {
			readUC();
			readUC();
			currency = readUC();
			readUC();
			readUH();
		}
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			GlobalTradeService.getInstance().sendHistory(player, GlobalTradeCurrency.of(currency));
	}
}
