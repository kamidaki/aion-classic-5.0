package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;

/**
 * S_GLOBAL_TRADE_HISTORY (0x145): vendas já recebidas nos últimos 28 dias numa moeda. Na captura veio logo depois do
 * S_GLOBAL_TRADE_COLLECT, com 499 bytes: o formato do S_GLOBAL_TRADE_SALESLOG, sem aviso, com a venda que acabou de ser recebida.
 */
public class SM_GLOBAL_TRADE_HISTORY extends SM_GLOBAL_TRADE_SALESLOG {

	public SM_GLOBAL_TRADE_HISTORY(GlobalTradeCurrency currency, long amount, int count, List<GlobalTradeListing> entries) {
		super(currency, REPLY, amount, count, entries);
	}
}
