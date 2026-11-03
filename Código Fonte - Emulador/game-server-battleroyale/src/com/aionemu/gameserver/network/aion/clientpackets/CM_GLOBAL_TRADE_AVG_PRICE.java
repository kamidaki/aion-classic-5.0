package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_AVG_PRICE, decodificado 0x103 (cru 0x1F1): [D objeto][D moeda], ao pôr um item na aba de registro (2 de 2 na captura).
 */
public class CM_GLOBAL_TRADE_AVG_PRICE extends AionClientPacket {

	private int itemObjId;
	private int currency;

	public CM_GLOBAL_TRADE_AVG_PRICE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjId = readD();
		currency = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			GlobalTradeService.getInstance().sendAveragePrice(player, itemObjId, GlobalTradeCurrency.of(currency));
	}
}
