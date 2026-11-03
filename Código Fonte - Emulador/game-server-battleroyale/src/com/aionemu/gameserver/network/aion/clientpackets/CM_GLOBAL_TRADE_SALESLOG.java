package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_SALESLOG, decodificado 0x101 (cru 0x1F3), 6 bytes: [C][C][C moeda][C][H]. O cliente pede as moedas 0 e 1 logo depois do
 * C_LEVEL_READY (168 pacotes em 45 capturas) e ao abrir a aba de receitas; respondido pelo S_GLOBAL_TRADE_SALESLOG (0x141). Na captura, a
 * venda em kinah veio na resposta da moeda 1.
 */
public class CM_GLOBAL_TRADE_SALESLOG extends AionClientPacket {

	private int currency = -1;

	public CM_GLOBAL_TRADE_SALESLOG(int opcode, Set<State> validStates) {
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
			GlobalTradeService.getInstance().sendSalesLog(player, GlobalTradeCurrency.of(currency));
	}
}
