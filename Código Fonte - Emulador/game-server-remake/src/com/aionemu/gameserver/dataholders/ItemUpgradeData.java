package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

import com.aionemu.gameserver.model.templates.item.ItemUpgradeTemplate;

/**
 * Receitas do Ascend (items/item_upgrade.xml, gerado do client_item_upgrade.xml).
 */
@XmlRootElement(name = "item_upgrades")
@XmlAccessorType(XmlAccessType.FIELD)
public class ItemUpgradeData {

	@XmlElement(name = "upgrade")
	private List<ItemUpgradeTemplate> templates = new ArrayList<>();

	@XmlTransient
	private final Map<Integer, ItemUpgradeTemplate> byId = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (ItemUpgradeTemplate template : templates) {
			if (byId.put(template.getId(), template) != null)
				throw new IllegalArgumentException("Duplicate item upgrade recipe " + template.getId());
			for (ItemUpgradeTemplate.Option option : template.getOptions()) {
				int total = option.getResults().stream().mapToInt(ItemUpgradeTemplate.Result::getRate).sum();
				if (total != 10000)
					throw new IllegalArgumentException("Invalid item upgrade recipe " + template.getId() + ": rates sum " + total);
			}
		}
		templates = null;
	}

	public ItemUpgradeTemplate getTemplate(int id) {
		return byId.get(id);
	}

	public int size() {
		return byId.size();
	}
}
