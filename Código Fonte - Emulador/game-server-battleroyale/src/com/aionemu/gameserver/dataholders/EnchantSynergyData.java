package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeMap;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

import com.aionemu.gameserver.model.templates.item.EnchantSynergyLevel;

/**
 * Sinergia de encantamento (items/enchant_synergy.xml, gerado do client_accumulated_enchant_effect.xml): nível = soma dos encantamentos
 * dos itens equipados com accumulated_enchant_effect; vale o maior nível com sum <= soma.
 */
@XmlRootElement(name = "enchant_synergy")
@XmlAccessorType(XmlAccessType.FIELD)
public class EnchantSynergyData {

	@XmlList
	@XmlElement(name = "items")
	private List<Integer> items = new ArrayList<>();
	@XmlElement(name = "level")
	private List<EnchantSynergyLevel> levels = new ArrayList<>();

	@XmlTransient
	private final Set<Integer> itemIds = new HashSet<>();
	@XmlTransient
	private final TreeMap<Integer, EnchantSynergyLevel> bySum = new TreeMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		itemIds.addAll(items);
		for (EnchantSynergyLevel level : levels)
			if (bySum.put(level.getSum(), level) != null)
				throw new IllegalArgumentException("Duplicate enchant synergy level " + level.getSum());
		items = null;
		levels = null;
	}

	public boolean isSynergyItem(int itemId) {
		return itemIds.contains(itemId);
	}

	/**
	 * @return o nível para a soma dada, ou null abaixo do primeiro
	 */
	public EnchantSynergyLevel getLevel(int enchantSum) {
		var entry = bySum.floorEntry(enchantSum);
		return entry == null ? null : entry.getValue();
	}

	public int size() {
		return bySum.size();
	}
}
