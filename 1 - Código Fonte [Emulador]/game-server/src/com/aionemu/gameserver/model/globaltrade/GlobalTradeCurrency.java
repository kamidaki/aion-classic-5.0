package com.aionemu.gameserver.model.globaltrade;

/**
 * Moeda de um anúncio da Global Auction House, como vai no fio (C_GLOBAL_TRADE_COMMIT, C_GLOBAL_TRADE_LIST, C_GLOBAL_TRADE_AVG_PRICE).
 * Nas capturas, o anúncio com moeda 1 foi pago e recebido em kinah; a aba de kinah (pacotes de 1 milhão, categoria 9010000) lista com
 * moeda 0, a Luna (Quna) da loja.
 */
public enum GlobalTradeCurrency {

	LUNA(0),
	KINAH(1);

	private final int id;

	GlobalTradeCurrency(int id) {
		this.id = id;
	}

	public int getId() {
		return id;
	}

	/**
	 * @return null para valor que não é moeda
	 */
	public static GlobalTradeCurrency of(int id) {
		for (GlobalTradeCurrency currency : values())
			if (currency.id == id)
				return currency;
		return null;
	}
}
