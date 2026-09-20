package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;

import com.aionemu.gameserver.model.templates.item.DecomposableItemInfo;
import com.aionemu.gameserver.model.templates.item.ExtractedItemsCollection;
import com.aionemu.gameserver.model.templates.item.ResultedItem;

/**
 * @author Lost Academy Team & Durak
 */
@XmlRootElement(name = "decomposable_items")
@XmlAccessorType(XmlAccessType.FIELD)
public class DecomposableItemsData {

	@XmlElement(name = "decomposable")
	private List<DecomposableItemInfo> decomposableItemsTemplates;

	@XmlTransient
	private final Map<Integer, List<ExtractedItemsCollection>> decomposableItemsInfo = new HashMap<>();
	@XmlTransient
	private final Map<Integer, List<ResultedItem>> selectableDecomposables = new HashMap<>();
	@XmlTransient
	private final Map<Integer, DecomposableItemInfo> setDecomposables = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		decomposableItemsInfo.clear();
		setDecomposables.clear();
		for (DecomposableItemInfo template : decomposableItemsTemplates) {
			if (!template.getSets().isEmpty()) {
				setDecomposables.put(template.getItemId(), template);
				continue;
			}
			List<ExtractedItemsCollection> itemGroups = template.getItemsCollections();
			if (itemGroups != null) {
				if (template.isIsSelectable()) {
					selectableDecomposables.put(template.getItemId(), itemGroups.get(0).getItems());
				} else {
					decomposableItemsInfo.put(template.getItemId(), itemGroups);
				}
			}
		}
		decomposableItemsTemplates = null;
	}

	public int size() {
		return decomposableItemsInfo.size() + selectableDecomposables.size() + setDecomposables.size();
	}

	/**
	 * Caixa no formato do cliente 5.0 (sets), ou null se o item nao tem ou esta no formato antigo (items).
	 */
	public DecomposableItemInfo getSetDecomposable(int itemId) {
		return setDecomposables.get(itemId);
	}

	public List<ResultedItem> getSelectableItems(int itemId) {
		List<ResultedItem> items = selectableDecomposables.get(itemId);
		return items == null ? null : new ArrayList<>(items);
	}

	public List<ExtractedItemsCollection> getInfoByItemId(int itemId) {
		return decomposableItemsInfo.get(itemId);
	}
}
