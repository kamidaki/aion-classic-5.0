package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_AVG_PRICE (0x143), 32 bytes: [D objeto][Q 0][Q][Q][D moeda]. Nas capturas: (0, 200.000, 200.000.000) em kinah e
 * (0, 19.400, 19.400) em Luna para a mesma pedra de ressurreição. Lidos como preço médio e maior preço unitário, na mesma escala x100 do
 * preço médio da lista; o primeiro Q foi 0 nas duas.
 */
public class SM_GLOBAL_TRADE_AVG_PRICE extends AionServerPacket {

	private final int itemObjId;
	private final long averageX100;
	private final long maximumX100;
	private final GlobalTradeCurrency currency;

	public SM_GLOBAL_TRADE_AVG_PRICE(int itemObjId, long averageX100, long maximumX100, GlobalTradeCurrency currency) {
		this.itemObjId = itemObjId;
		this.averageX100 = averageX100;
		this.maximumX100 = maximumX100;
		this.currency = currency;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(itemObjId);
		writeQ(0);
		writeQ(averageX100);
		writeQ(maximumX100);
		writeD(currency.getId());
	}
}
