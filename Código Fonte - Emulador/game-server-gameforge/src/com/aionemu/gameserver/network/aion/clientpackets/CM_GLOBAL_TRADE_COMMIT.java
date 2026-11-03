package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_COMMIT, decodificado 0x117 (cru 0x1ED): [D objeto][Q preço total][Q quantidade][D moeda], 24 bytes (2 de 2 capturas).
 * O cru 0x1ED estava com o CM_GUILD_SEARCH da 4.x, que não fazia nada.
 */
public class CM_GLOBAL_TRADE_COMMIT extends AionClientPacket {

	private int itemObjId;
	private long price;
	private long count;
	private int currency;

	public CM_GLOBAL_TRADE_COMMIT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjId = readD();
		price = readQ();
		count = readQ();
		currency = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			GlobalTradeService.getInstance().commit(player, itemObjId, price, count, GlobalTradeCurrency.of(currency));
	}
}
