package com.aionemu.gameserver.model.templates.item;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "DecomposableItem")
public class DecomposableItemInfo {

	@XmlAttribute(name = "item_id")
	private int itemId;
	@XmlAttribute(name = "selectable")
	private boolean isSelectable = false;
	@XmlAttribute(name = "only_one")
	private boolean onlyOne = false;
	@XmlElement(name = "items")
	private List<ExtractedItemsCollection> itemsCollections;
	@XmlElement(name = "set")
	private List<DecomposableSet> sets;

	public int getItemId() {
		return itemId;
	}

	public boolean isIsSelectable() {
		return isSelectable;
	}

	public boolean isOnlyOne() {
		return onlyOne;
	}

	public List<ExtractedItemsCollection> getItemsCollections() {
		return itemsCollections;
	}

	public List<DecomposableSet> getSets() {
		return sets != null ? sets : Collections.emptyList();
	}

	/**
	 * Sets que valem para o jogador (raca, classe e nivel). Com only_one, so o primeiro deles.
	 */
	public List<DecomposableSet> getSetsFor(Player player) {
		List<DecomposableSet> result = new ArrayList<>();
		for (DecomposableSet set : getSets()) {
			if (set.appliesTo(player)) {
				result.add(set);
				if (onlyOne)
					break;
			}
		}
		return result;
	}

	/**
	 * Opcoes da janela de escolha (caixa selectable), na ordem do cliente: o indice que o C_SELECT_DISASSEMBLY_ITEM devolve aponta aqui.
	 */
	public List<DecomposableSetItem> getSelectableItemsFor(Player player) {
		List<DecomposableSetItem> result = new ArrayList<>();
		for (DecomposableSet set : getSetsFor(player))
			result.addAll(set.getItems());
		return result;
	}

	/**
	 * Sorteio de uma caixa comum: cada set que vale para o jogador passa com a sua chance e da um item pelo peso.
	 */
	public List<DecomposableSetItem> rollItemsFor(Player player) {
		List<DecomposableSetItem> result = new ArrayList<>();
		for (DecomposableSet set : getSetsFor(player)) {
			if (set.roll()) {
				DecomposableSetItem item = set.pickItem();
				if (item != null)
					result.add(item);
			}
		}
		return result;
	}
}
