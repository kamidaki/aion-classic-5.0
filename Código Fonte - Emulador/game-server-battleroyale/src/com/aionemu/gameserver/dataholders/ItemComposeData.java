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

import com.aionemu.gameserver.model.templates.item.ItemComposeRecipe;

/**
 * Receitas do Altar of Transcendence (items/item_compose.xml, gerado do client_item_compose.xml).
 */
@XmlRootElement(name = "item_composes")
@XmlAccessorType(XmlAccessType.FIELD)
public class ItemComposeData {

	@XmlElement(name = "compose")
	private List<ItemComposeRecipe> recipes = new ArrayList<>();

	@XmlTransient
	private final Map<Integer, ItemComposeRecipe> byId = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (ItemComposeRecipe recipe : recipes) {
			if (byId.put(recipe.getId(), recipe) != null)
				throw new IllegalArgumentException("Duplicate item compose recipe " + recipe.getId());
			int total = recipe.getResults().stream().mapToInt(ItemComposeRecipe.Result::getRate).sum();
			if (total != 10000 || !recipe.hasMaterials())
				throw new IllegalArgumentException("Invalid item compose recipe " + recipe.getId());
		}
		recipes = null;
	}

	public ItemComposeRecipe getRecipe(int id) {
		return byId.get(id);
	}

	public int size() {
		return byId.size();
	}
}
