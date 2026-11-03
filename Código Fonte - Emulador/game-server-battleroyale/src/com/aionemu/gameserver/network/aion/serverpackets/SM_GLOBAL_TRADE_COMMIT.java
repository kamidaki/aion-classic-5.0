package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_COMMIT (0x13F), 478 bytes, depois do registro (4 de 4 nas capturas): [C 0], o anúncio
 * ({@link GlobalTradeItemDetail#writeRegistered}) e [D moeda].
 */
public class SM_GLOBAL_TRADE_COMMIT extends AionServerPacket {

	private final GlobalTradeListing listing;

	public SM_GLOBAL_TRADE_COMMIT(GlobalTradeListing listing) {
		this.listing = listing;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0);
		GlobalTradeItemDetail.writeRegistered(getBuf(), listing);
		writeD(listing.getCurrency().getId());
	}
}
