package com.aionemu.gameserver.services.item;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.templates.item.ItemSkillSet;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.utils.idfactory.IDFactory;

/**
 * @author Lost Academy Team & Durak
 */
public class ItemFactory {

	private static final Logger log = LoggerFactory.getLogger(ItemFactory.class);

	public static final Item newItem(int itemId) {
		ItemTemplate itemTemplate = DataManager.ITEM_DATA.getItemTemplate(itemId);
		if (itemTemplate == null) {
			log.error("Item was not populated correctly. Item template is missing for item id: " + itemId);
			return null;
		}
		Item item = new Item(IDFactory.getInstance().nextId(), itemTemplate);
		// 5.0 "Assign Skill on Loot": o item do conjunto já nasce com uma skill sorteada (D no offset 60 do bloco 0x0B)
		ItemSkillSet skillSet = DataManager.ITEM_SKILL_SET_DATA.getSkillSet(itemId);
		if (skillSet != null)
			item.setBuffSkill(skillSet.roll());
		return item;
	}

	public static Item newItem(int itemId, long count) {
		Item item = newItem(itemId);
		item.setItemCount(calculateCount(item.getItemTemplate(), count));
		return item;
	}

	private static final long calculateCount(ItemTemplate itemTemplate, long count) {
		long maxStackCount = itemTemplate.getMaxStackCount();
		if (count > maxStackCount && !itemTemplate.isKinah())
			count = maxStackCount;
		return count;
	}

}
