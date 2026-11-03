package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;
import com.aionemu.gameserver.model.templates.item.SielHammerTable;

@XmlRootElement(name = "siel_hammer")
@XmlAccessorType(XmlAccessType.FIELD)
public class SielHammerData {
	@XmlElement(name = "table")
	private List<SielHammerTable> tables = new ArrayList<>();
	@XmlElement(name = "item")
	private List<EligibleItem> items = new ArrayList<>();
	@XmlTransient
	private final Map<Integer, SielHammerTable> byId = new HashMap<>();
	@XmlTransient
	private final Map<Integer, SielHammerTable> byItem = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (var table : tables) {
			if (table.getId() <= 0 || table.getKinah() < 0 || table.getBands().isEmpty() || byId.put(table.getId(), table) != null)
				throw new IllegalArgumentException("Invalid Hammer table " + table.getId());
			int previous = -1;
			for (var band : table.getBands()) {
				if (band.getMinimum() <= previous || band.getMaximum() < band.getMinimum()
					|| band.getResults().stream().mapToInt(r -> r.getProbability()).sum() != 1000)
					throw new IllegalArgumentException("Invalid Hammer band " + table.getId());
				previous = band.getMaximum();
				for (var reward : band.getResults()) validate(reward);
				if (band.getBonus() != null) validate(band.getBonus());
			}
		}
		for (var item : items) {
			var table = byId.get(item.tableId);
			if (item.itemId <= 0 || table == null || byItem.put(item.itemId, table) != null)
				throw new IllegalArgumentException("Invalid Hammer eligible item " + item.itemId);
		}
		tables = null;
		items = null;
	}
	private static void validate(SielHammerTable.Reward reward) {
		if (reward.getItemId() <= 0 || reward.getCount() <= 0 || reward.getProbability() < 0 || reward.getProbability() > 1000)
			throw new IllegalArgumentException("Invalid Hammer reward");
	}
	public SielHammerTable getTable(int itemId) { return byItem.get(itemId); }
	public int tableCount() { return byId.size(); }
	public int itemCount() { return byItem.size(); }

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class EligibleItem {
		@XmlAttribute(name = "item_id", required = true)
		private int itemId;
		@XmlAttribute(name = "table_id", required = true)
		private int tableId;
	}
}
