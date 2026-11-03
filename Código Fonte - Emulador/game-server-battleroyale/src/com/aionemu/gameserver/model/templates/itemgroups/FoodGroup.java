package com.aionemu.gameserver.model.templates.itemgroups;

import java.util.Collections;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.templates.rewards.FoodItem;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "FoodGroup")
public class FoodGroup extends BonusItemGroup {

	@XmlElement(name = "item")
	private List<FoodItem> items;

	@Override
	public List<FoodItem> getItems() {
		return items == null ? Collections.emptyList() : items;
	}

}
