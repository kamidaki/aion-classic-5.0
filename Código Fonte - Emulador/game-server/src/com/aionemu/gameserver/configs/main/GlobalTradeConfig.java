package com.aionemu.gameserver.configs.main;

import com.aionemu.commons.configuration.Property;

/**
 * Global Auction House (Classic 5.0). Os padrões vêm das capturas oficiais de 2026-09-11; o que não foi medido está marcado.
 */
public class GlobalTradeConfig {

	@Property(key = "gameserver.globaltrade.enable", defaultValue = "true")
	public static boolean ENABLE;

	/**
	 * STR_MSG_WORLD_VENDOR_BELOW_STANDARD: nível 10 e classe já trocada.
	 */
	@Property(key = "gameserver.globaltrade.min.level", defaultValue = "10")
	public static int MIN_LEVEL;

	/**
	 * STR_MSG_WORLD_VENDOR_FULL_BASKET: no máximo 15 itens anunciados ao mesmo tempo.
	 */
	@Property(key = "gameserver.globaltrade.max.listings", defaultValue = "15")
	public static int MAX_LISTINGS;

	/**
	 * Taxa de registro de anúncio em kinah, em 1/10000 do preço. Captura: 2.420 de taxa para 200.000 de preço.
	 */
	@Property(key = "gameserver.globaltrade.register.fee.permyriad", defaultValue = "121")
	public static int REGISTER_FEE_PERMYRIAD;

	/**
	 * Taxa de registro de anúncio em Quna, cobrada em kinah por Quna do preço. Captura (2 de 2): 6.050 kinah para 10 Quna. Só esse preço foi
	 * amostrado; a fórmula do oficial pode não ser linear.
	 */
	@Property(key = "gameserver.globaltrade.quna.register.fee", defaultValue = "605")
	public static long QUNA_REGISTER_FEE;

	/**
	 * Taxa descontada da venda, em 1/10000 do preço. Captura: venda de 200.000 rendeu 184.000.
	 */
	@Property(key = "gameserver.globaltrade.sale.fee.permyriad", defaultValue = "800")
	public static int SALE_FEE_PERMYRIAD;

	/**
	 * Duração do anúncio. Não medido: o S_GLOBAL_TRADE_COMMIT traz um byte 8 antes do item, lido como dias.
	 */
	@Property(key = "gameserver.globaltrade.listing.days", defaultValue = "8")
	public static int LISTING_DAYS;

	/**
	 * Preço total máximo de um anúncio.
	 */
	@Property(key = "gameserver.globaltrade.max.price", defaultValue = "99999999999")
	public static long MAX_PRICE;

	/**
	 * Limite semanal de kinah do S_GLOBAL_TRADE_STATE (STR_MSG_WORLD_VENDOR_GOLD_EXCESS: 1 bilhão por semana).
	 */
	@Property(key = "gameserver.globaltrade.weekly.kinah.limit", defaultValue = "1000000000")
	public static long WEEKLY_KINAH_LIMIT;
}
