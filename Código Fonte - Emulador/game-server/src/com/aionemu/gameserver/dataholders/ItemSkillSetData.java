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

import com.aionemu.gameserver.model.templates.item.ItemSkillSet;

/**
 * Skill de equipamento por item (items/item_skill_sets.xml, gerado do client_item_skill_enchant.xml + skill_set_name dos itens).
 */
@XmlRootElement(name = "item_skill_sets")
@XmlAccessorType(XmlAccessType.FIELD)
public class ItemSkillSetData {

	@XmlElement(name = "skill_set")
	private List<ItemSkillSet> sets = new ArrayList<>();

	@XmlTransient
	private final Map<Integer, ItemSkillSet> byItemId = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (ItemSkillSet set : sets) {
			if (set.getSkills().isEmpty() || set.getSkills().stream().mapToInt(ItemSkillSet.ItemSkillSetSkill::getProb).sum() <= 0)
				throw new IllegalArgumentException("Invalid item skill set " + set.getName());
			for (int itemId : set.getItems())
				if (byItemId.put(itemId, set) != null)
					throw new IllegalArgumentException("Item " + itemId + " in more than one item skill set");
		}
		sets = null;
	}

	public ItemSkillSet getSkillSet(int itemId) {
		return byItemId.get(itemId);
	}

	public int size() {
		return byItemId.size();
	}
}
