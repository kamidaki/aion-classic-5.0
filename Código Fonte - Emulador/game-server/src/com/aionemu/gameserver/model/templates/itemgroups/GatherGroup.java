package com.aionemu.gameserver.model.templates.itemgroups;

import java.util.Collections;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "GatherGroup")
public class GatherGroup extends BonusItemGroup {

	@XmlElement(name = "item")
	private List<ItemRaceEntry> items;

	@Override
	public List<ItemRaceEntry> getItems() {
		return items == null ? Collections.emptyList() : items;
	}
}
