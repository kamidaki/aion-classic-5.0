package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

import com.aionemu.gameserver.model.drop.FlyRewardType;
import com.aionemu.gameserver.model.templates.fly.FlyDropTemplate;

@XmlRootElement(name = "fly_loot")
@XmlAccessorType(XmlAccessType.FIELD)
public class FlyLootData {

	@XmlElement(name = "drop")
	private List<FlyDropTemplate> drops;

	@XmlTransient
	private final Map<FlyRewardType, List<FlyDropTemplate>> dropsByType = new EnumMap<>(FlyRewardType.class);

	@XmlTransient
	private final Map<Integer, FlyDropTemplate> dropsByItemId = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		if (drops == null)
			return;
		for (FlyDropTemplate drop : drops) {
			dropsByType.computeIfAbsent(drop.getType(), key -> new ArrayList<>()).add(drop);
			dropsByItemId.putIfAbsent(drop.getItemId(), drop);
		}
		for (List<FlyDropTemplate> list : dropsByType.values()) {
			list.sort((a, b) -> Integer.compare(a.getRecommendedLevel(), b.getRecommendedLevel()));
		}
		drops = null;
	}

	public List<FlyDropTemplate> getAllDrops() {
		return new ArrayList<>(dropsByItemId.values());
	}

	public List<FlyDropTemplate> getDrops(FlyRewardType type) {
		return dropsByType.getOrDefault(type, List.of());
	}

	public FlyDropTemplate getTemplate(int itemId) {
		return dropsByItemId.get(itemId);
	}

	public boolean isEmpty() {
		return dropsByItemId.isEmpty();
	}

	public int size() {
		return dropsByItemId.size();
	}
}
