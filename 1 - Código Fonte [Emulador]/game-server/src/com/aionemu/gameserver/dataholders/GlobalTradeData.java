package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;

/**
 * Itens anunciáveis na Global Auction House, por categoria (items/global_trade.xml, gerado do client_items.xml).
 */
@XmlRootElement(name = "global_trade")
@XmlAccessorType(XmlAccessType.FIELD)
public class GlobalTradeData {

	@XmlElement(name = "category")
	private List<Category> categories = new ArrayList<>();

	@XmlTransient
	private final Map<Integer, Integer> categoryByItem = new HashMap<>();
	@XmlTransient
	private final Set<Integer> kinahItems = new HashSet<>();
	@XmlTransient
	private final Set<Integer> lunaItems = new HashSet<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (Category category : categories) {
			for (List<Integer> ids : List.of(category.kinah, category.luna))
				for (int itemId : ids) {
					Integer previous = categoryByItem.put(itemId, category.id);
					if (previous != null && previous != category.id)
						throw new IllegalArgumentException("Global trade item " + itemId + " in categories " + previous + " and " + category.id);
				}
			kinahItems.addAll(category.kinah);
			lunaItems.addAll(category.luna);
		}
		categories = null;
	}

	public boolean canRegister(int itemId, GlobalTradeCurrency currency) {
		return (currency == GlobalTradeCurrency.KINAH ? kinahItems : lunaItems).contains(itemId);
	}

	/**
	 * @return vendor_category_index do cliente; 0 para item anunciável sem categoria (só aparece na busca por nome)
	 */
	public int getCategory(int itemId) {
		return categoryByItem.getOrDefault(itemId, 0);
	}

	public int size() {
		return categoryByItem.size();
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	private static class Category {

		@XmlAttribute(required = true)
		private int id;

		@XmlList
		@XmlElement
		private List<Integer> kinah = new ArrayList<>();

		@XmlList
		@XmlElement
		private List<Integer> luna = new ArrayList<>();
	}
}
