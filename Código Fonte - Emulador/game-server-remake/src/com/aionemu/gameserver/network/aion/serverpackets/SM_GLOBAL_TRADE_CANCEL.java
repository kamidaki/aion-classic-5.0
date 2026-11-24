package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_CANCEL (0x140): [C 0][Q anúncio], por último no cancelamento, depois do item de volta ao cubo (cabeçalho 0x9E) e da
 * mensagem 1401790 (2 de 2 na captura de 2026-09-21).
 */
public class SM_GLOBAL_TRADE_CANCEL extends AionServerPacket {

	private final long listingId;

	public SM_GLOBAL_TRADE_CANCEL(long listingId) {
		this.listingId = listingId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0);
		writeQ(listingId);
	}
}
