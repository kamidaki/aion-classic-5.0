package com.aionemu.gameserver.model.templates.item;

import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;


@XmlType(name = "ResultedItemsCollection")
public class ResultedItemsCollection {

	@XmlElement(name = "item")
	protected ArrayList<ResultedItem> items;
	@XmlElement(name = "item_set")
	protected ArrayList<ResultedItemSet> item_set;

	public Collection<ResultedItem> getItems() {
		return items != null ? items : Collections.<ResultedItem> emptyList();
	}

	public Collection<ResultedItemSet> getItemSet() {
		return item_set != null ? item_set : Collections.<ResultedItemSet> emptyList();
	}
}
