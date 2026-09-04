package com.aionemu.gameserver.model.broker.filter;

import com.aionemu.gameserver.model.templates.item.ItemTemplate;


public class BrokerAllAcceptFilter extends BrokerFilter {

	@Override
	public boolean accept(ItemTemplate template) {
		return true;
	}
}
