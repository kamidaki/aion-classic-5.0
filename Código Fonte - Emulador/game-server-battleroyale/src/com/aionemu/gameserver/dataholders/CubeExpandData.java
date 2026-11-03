package com.aionemu.gameserver.dataholders;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;

import com.aionemu.gameserver.model.templates.StorageExpansionTemplate;

/**
 * @author Lost Academy Team & Durak
 */
@XmlRootElement(name = "cube_expander")
@XmlAccessorType(XmlAccessType.FIELD)
public class CubeExpandData {

	@XmlElement(name = "expansion_npc")
	private List<StorageExpansionTemplate> expansionTemplates;

	@XmlTransient
	private final Map<Integer, StorageExpansionTemplate> expansionTemplatesByNpcId = new HashMap<>();
	@XmlTransient
	private final Map<Integer, Integer> pricesByExpansionLevel = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		for (StorageExpansionTemplate expansionTemplate : expansionTemplates) {
			for (int npcId : expansionTemplate.getNpcIds())
				expansionTemplatesByNpcId.put(npcId, expansionTemplate);
			for (int level = expansionTemplate.getMinExpansionLevel(); level <= expansionTemplate.getMaxExpansionLevel(); level++) {
				Integer price = expansionTemplate.getPrice(level);
				if (price != null)
					pricesByExpansionLevel.putIfAbsent(level, price);
			}
		}
		expansionTemplates = null;
	}

	public int size() {
		return expansionTemplatesByNpcId.size();
	}

	public StorageExpansionTemplate getCubeExpansionTemplate(int id) {
		return expansionTemplatesByNpcId.get(id);
	}

	/**
	 * Classic 5.0 also exposes paid cube expansion directly from the inventory UI,
	 * without an NPC object in the request. The price still follows the same
	 * expansion-level table used by cube expander NPCs.
	 */
	public Integer getPrice(int expansionLevel) {
		return pricesByExpansionLevel.get(expansionLevel);
	}
}
