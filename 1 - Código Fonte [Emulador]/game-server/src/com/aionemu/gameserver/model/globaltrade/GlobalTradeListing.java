package com.aionemu.gameserver.model.globaltrade;

import com.aionemu.gameserver.model.gameobjects.Item;

/**
 * Um anúncio da Global Auction House. O item anunciado fica no inventory com o local {@code GLOBAL_TRADE} e o vendedor como dono até
 * ser comprado (vai para o comprador), cancelado ou vencido (volta ao vendedor). A linha do anúncio fica como histórico de venda.
 * <p>
 * Os campos mutáveis só mudam dentro do lock do GlobalTradeService.
 */
public final class GlobalTradeListing {

	public enum State {
		/** à venda */
		LISTED,
		/** vendido, receita ainda não recebida pelo vendedor */
		SOLD,
		/** vendido e receita recebida */
		COLLECTED,
		CANCELED,
		EXPIRED
	}

	private final long id;
	private final int sellerId;
	private final int itemUniqueId;
	private final int itemId;
	private final long count;
	private final long price;
	private final GlobalTradeCurrency currency;
	private final int category;
	private final long registerFee;
	private final long registerTime;
	private final long expireTime;

	private Item item;
	private State state;
	private int buyerId;
	private long soldTime;
	private long saleFee;
	private long collectedTime;

	public GlobalTradeListing(long id, int sellerId, int itemUniqueId, int itemId, long count, long price, GlobalTradeCurrency currency,
		int category, long registerFee, long registerTime, long expireTime, State state, int buyerId, long soldTime, long saleFee,
		long collectedTime) {
		this.id = id;
		this.sellerId = sellerId;
		this.itemUniqueId = itemUniqueId;
		this.itemId = itemId;
		this.count = count;
		this.price = price;
		this.currency = currency;
		this.category = category;
		this.registerFee = registerFee;
		this.registerTime = registerTime;
		this.expireTime = expireTime;
		this.state = state;
		this.buyerId = buyerId;
		this.soldTime = soldTime;
		this.saleFee = saleFee;
		this.collectedTime = collectedTime;
	}

	public long getId() {
		return id;
	}

	public int getSellerId() {
		return sellerId;
	}

	public int getItemUniqueId() {
		return itemUniqueId;
	}

	public int getItemId() {
		return itemId;
	}

	public long getCount() {
		return count;
	}

	/**
	 * @return preço total do anúncio (a quantidade inteira vai junto na compra)
	 */
	public long getPrice() {
		return price;
	}

	public GlobalTradeCurrency getCurrency() {
		return currency;
	}

	public int getCategory() {
		return category;
	}

	public long getRegisterFee() {
		return registerFee;
	}

	public long getRegisterTime() {
		return registerTime;
	}

	public long getExpireTime() {
		return expireTime;
	}

	public Item getItem() {
		return item;
	}

	public void setItem(Item item) {
		this.item = item;
	}

	public State getState() {
		return state;
	}

	public int getBuyerId() {
		return buyerId;
	}

	public long getSoldTime() {
		return soldTime;
	}

	public long getSaleFee() {
		return saleFee;
	}

	/**
	 * @return o que o vendedor recebe: preço menos a taxa da venda
	 */
	public long getRevenue() {
		return price - saleFee;
	}

	public long getCollectedTime() {
		return collectedTime;
	}

	public void markSold(int buyerId, long soldTime, long saleFee) {
		this.state = State.SOLD;
		this.buyerId = buyerId;
		this.soldTime = soldTime;
		this.saleFee = saleFee;
	}

	/**
	 * Desfaz o {@link #markSold} quando a venda não foi gravada.
	 */
	public void unmarkSold() {
		this.state = State.LISTED;
		this.buyerId = 0;
		this.soldTime = 0;
		this.saleFee = 0;
	}

	public void markCollected(long collectedTime) {
		this.state = State.COLLECTED;
		this.collectedTime = collectedTime;
	}

	/**
	 * Desfaz o {@link #markCollected} quando o recebimento não foi gravado.
	 */
	public void unmarkCollected() {
		this.state = State.SOLD;
		this.collectedTime = 0;
	}

	public void setState(State state) {
		this.state = state;
	}

	@Override
	public String toString() {
		return "GlobalTradeListing[id=" + id + ", seller=" + sellerId + ", item=" + itemId + " x" + count + ", price=" + price + " " + currency
			+ ", state=" + state + "]";
	}
}
