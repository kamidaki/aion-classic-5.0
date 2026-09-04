package com.aionemu.gameserver.model.limiteditems;

import java.util.List;
import java.util.ArrayList;


public class LimitedTradeNpc {

	private List<LimitedItem> limitedItems;

	public LimitedTradeNpc(List<LimitedItem> limitedItems) {
		this.limitedItems = limitedItems;
		
	}

	public void putLimitedItems(List<LimitedItem> limitedItems) {
		this.limitedItems.addAll(limitedItems);
	}

	public List<LimitedItem> getLimitedItems() {
		return limitedItems;
	}
}
