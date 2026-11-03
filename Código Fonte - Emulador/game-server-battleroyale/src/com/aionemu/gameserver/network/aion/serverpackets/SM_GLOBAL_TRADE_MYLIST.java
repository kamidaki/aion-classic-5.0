package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_MYLIST (0x13D): anúncios do jogador numa moeda, resposta do C_GLOBAL_TRADE_MYLIST (0x115 [D moeda]).
 * <p>
 * [C 1][C 1][C moeda][C 0][H 0][H anúncios] e cada anúncio no registro de 473 bytes ({@link GlobalTradeItemDetail#writeRegistered}):
 * 8 bytes sem anúncio, 481 com um (captura de 2026-09-21, um em Luna e um em kinah).
 */
public class SM_GLOBAL_TRADE_MYLIST extends AionServerPacket {

	public static final int MAX_ENTRIES = 15;

	private final GlobalTradeCurrency currency;
	private final List<GlobalTradeListing> entries;

	public SM_GLOBAL_TRADE_MYLIST(GlobalTradeCurrency currency, List<GlobalTradeListing> entries) {
		this.currency = currency;
		this.entries = entries.size() > MAX_ENTRIES ? entries.subList(0, MAX_ENTRIES) : entries;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(1);
		writeC(1);
		writeC(currency.getId());
		writeC(0);
		writeH(0);
		writeH(entries.size());
		for (GlobalTradeListing listing : entries)
			GlobalTradeItemDetail.writeRegistered(getBuf(), listing);
	}
}
