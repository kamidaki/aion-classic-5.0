package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_SALESLOG (0x141): vendas de uma moeda com receita a receber, resposta do C_GLOBAL_TRADE_SALESLOG (0x101).
 * <p>
 * Cabeçalho de 23 bytes (270 pacotes nas capturas): [Q valor][D vendas][C 0][C 0][C aviso][C 1][C 1][C moeda][C 0][C 0][C 0][H entradas].
 * No login o servidor manda as duas moedas como aviso (C 1, valor bruto, sem entradas) e o cliente pede as duas. Com 1 venda de 200.000 em
 * kinah: aviso da moeda 1 com 200.000 e 0 vendas; resposta com 184.000 (já sem a taxa de 8%), 1 venda e 1 entrada.
 * <p>
 * Entrada de 476 bytes: [D item][Q preço][D quantidade][D 0][D minutos desde 1970 da venda][Q taxa da venda][441 bytes de detalhe][3 bytes 0].
 * O detalhe da venda capturada é lixo de memória: o item já é do comprador.
 */
public class SM_GLOBAL_TRADE_SALESLOG extends AionServerPacket {

	public static final int MAX_ENTRIES = 15;

	private final GlobalTradeCurrency currency;
	private final boolean notice;
	private final long amount;
	private final int count;
	private final List<GlobalTradeListing> entries;

	public SM_GLOBAL_TRADE_SALESLOG(GlobalTradeCurrency currency, boolean notice, long amount, int count, List<GlobalTradeListing> entries) {
		this.currency = currency;
		this.notice = notice;
		this.amount = amount;
		this.count = count;
		this.entries = entries.size() > MAX_ENTRIES ? entries.subList(0, MAX_ENTRIES) : entries;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeQ(amount);
		writeD(count);
		writeC(0);
		writeC(0);
		writeC(notice ? 1 : 0);
		writeC(1);
		writeC(1);
		writeC(currency.getId());
		writeC(0);
		writeC(0);
		writeC(0);
		writeH(entries.size());
		for (GlobalTradeListing listing : entries) {
			writeD(listing.getItemId());
			writeQ(listing.getPrice());
			writeD((int) listing.getCount());
			writeD(0);
			writeD((int) (listing.getSoldTime() / 60000));
			writeQ(listing.getSaleFee());
			GlobalTradeItemDetail.write(getBuf(), null, listing.getItemId());
			writeB(new byte[3]);
		}
	}
}
