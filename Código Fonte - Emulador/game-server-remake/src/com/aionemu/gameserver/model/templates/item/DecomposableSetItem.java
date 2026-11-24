package com.aionemu.gameserver.model.templates.item;

import java.util.Collections;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService.ItemUpdatePredicate;
import com.aionemu.gameserver.services.item.ItemSocketService;

/**
 * Item de um {@link DecomposableSet}: quantidade, peso na lista e, pelo client_disassembly_item_Customize, o encanto e as manastones com
 * que ele sai da caixa.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "DecomposableSetItem")
public class DecomposableSetItem {

	@XmlAttribute(name = "id", required = true)
	private int itemId;
	@XmlAttribute(name = "count")
	private int count = 1;
	@XmlAttribute(name = "rate")
	private int rate = 10000;
	@XmlAttribute(name = "enchant")
	private int enchant;
	@XmlList
	@XmlAttribute(name = "manastones")
	private List<Integer> manastones;

	public int getItemId() {
		return itemId;
	}

	public int getCount() {
		return count;
	}

	public int getRate() {
		return rate;
	}

	public int getEnchant() {
		return enchant;
	}

	public List<Integer> getManastones() {
		return manastones != null ? manastones : Collections.emptyList();
	}

	public ItemUpdatePredicate newUpdatePredicate() {
		return new ItemUpdatePredicate(ItemAddType.DECOMPOSABLE, ItemUpdateType.INC_ITEM_DECOMPOSE) {

			@Override
			public boolean changeItem(Item item) {
				if (enchant > 0)
					item.setEnchantLevel(enchant);
				for (int stoneId : getManastones())
					ItemSocketService.addManaStone(item, stoneId, false);
				return true;
			}
		};
	}
}
