package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_LIST (0x13C), resposta do C_GLOBAL_TRADE_LIST. Até 18 anúncios por página, em pacotes de no máximo 15.
 * <p>
 * Cabeçalho de 19 bytes (48 pacotes nas capturas): [D total][C busca por itemIds][H página][D categoria, 0 na busca][H entradas neste
 * pacote][C primeiro][C último][4 bytes do pedido: C moeda, C, H]. Entrada de 480 bytes: [Q anúncio][D item][Q preço total][Q preço médio
 * unitário x100][D quantidade][D 0][441 bytes de detalhe][3 bytes 0].
 */
public class SM_GLOBAL_TRADE_LIST extends AionServerPacket {

	public record Entry(GlobalTradeListing listing, long averageUnitPriceX100) {
	}

	private final int total;
	private final boolean search;
	private final int page;
	private final int category;
	private final boolean first;
	private final boolean last;
	private final byte[] requestTail;
	private final List<Entry> entries;

	public SM_GLOBAL_TRADE_LIST(int total, boolean search, int page, int category, boolean first, boolean last, byte[] requestTail,
		List<Entry> entries) {
		this.total = total;
		this.search = search;
		this.page = page;
		this.category = category;
		this.first = first;
		this.last = last;
		this.requestTail = requestTail;
		this.entries = entries;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(total);
		writeC(search ? 1 : 0);
		writeH(page);
		writeD(search ? 0 : category);
		writeH(entries.size());
		writeC(first ? 1 : 0);
		writeC(last ? 1 : 0);
		writeB(requestTail);
		for (Entry entry : entries) {
			GlobalTradeListing listing = entry.listing();
			writeQ(listing.getId());
			writeD(listing.getItemId());
			writeQ(listing.getPrice());
			writeQ(entry.averageUnitPriceX100());
			writeD((int) listing.getCount());
			writeD(0);
			GlobalTradeItemDetail.write(getBuf(), listing.getItem(), listing.getItemId());
			writeB(new byte[3]);
		}
	}
}
