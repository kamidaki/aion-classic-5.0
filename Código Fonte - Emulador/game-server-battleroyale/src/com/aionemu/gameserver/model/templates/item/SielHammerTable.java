package com.aionemu.gameserver.model.templates.item;

import java.util.ArrayList;
import java.util.List;
import javax.xml.bind.annotation.*;

/** Official crushing tables: independent normal/bonus rolls, denominator 1000. */
@XmlAccessorType(XmlAccessType.FIELD)
public class SielHammerTable {

	@XmlAttribute(required = true)
	private int id;
	@XmlAttribute(required = true)
	private long kinah;
	@XmlElement(name = "band")
	private List<Band> bands = new ArrayList<>();
	public int getId() { return id; }
	public long getKinah() { return kinah; }
	public List<Band> getBands() { return bands; }
	public Band getBand(int enchantment) {
		return bands.stream().filter(b -> enchantment >= b.minimum && enchantment <= b.maximum).findFirst().orElse(null);
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Band {
		@XmlAttribute(required = true)
		private int minimum;
		@XmlAttribute(required = true)
		private int maximum;
		@XmlElement(name = "result")
		private List<Reward> results = new ArrayList<>();
		@XmlElement(name = "bonus")
		private Reward bonus;
		public int getMinimum() { return minimum; }
		public int getMaximum() { return maximum; }
		public List<Reward> getResults() { return results; }
		public Reward getBonus() { return bonus; }
		public Reward selectResult(int roll) {
			if (roll < 0 || roll >= 1000) throw new IllegalArgumentException("Invalid Hammer roll");
			for (Reward result : results) {
				if (roll < result.probability) return result;
				roll -= result.probability;
			}
			throw new IllegalStateException("Invalid Hammer probability total");
		}
		public boolean hasBonus(int roll) {
			if (roll < 0 || roll >= 1000) throw new IllegalArgumentException("Invalid Hammer bonus roll");
			return bonus != null && roll < bonus.probability;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Reward {
		@XmlAttribute(name = "item_id", required = true)
		private int itemId;
		@XmlAttribute(required = true)
		private long count;
		@XmlAttribute(required = true)
		private int probability;
		public int getItemId() { return itemId; }
		public long getCount() { return count; }
		public int getProbability() { return probability; }
	}
}
