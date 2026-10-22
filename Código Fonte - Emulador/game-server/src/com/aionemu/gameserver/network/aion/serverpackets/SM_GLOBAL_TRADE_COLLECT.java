package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_COLLECT (0x142), depois de receber as vendas: [C 0][D moeda] (captura: 00 01000000 no recebimento em kinah).
 * <p>
 * O D é a moeda, não a quantidade de vendas: o tratador do Game.dll (0x8BCD00) limpa as vendas a receber dessa moeda (0x823530) e
 * redesenha a aba Sold Items dela (+0x500 kinah, +0x4F8 Quna). Com a quantidade, 2 vendas ou mais deixavam a aba sem atualizar.
 */
public class SM_GLOBAL_TRADE_COLLECT extends AionServerPacket {

	private final GlobalTradeCurrency currency;

	public SM_GLOBAL_TRADE_COLLECT(GlobalTradeCurrency currency) {
		this.currency = currency;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0);
		writeD(currency.getId());
	}
}
