package com.aionemu.gameserver.model.broker.filter;

import com.aionemu.gameserver.model.templates.item.ItemTemplate;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class BrokerFilter {

	/**
	 * @param template
	 * @return
	 */
	public abstract boolean accept(ItemTemplate template);
}
