package com.aionemu.gameserver.model.templates.item;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.LinkedHashMap;
import javax.xml.bind.annotation.*;

/** Server-authoritative special crafting costs and weighted products (probability denominator: 10000). */
@XmlAccessorType(XmlAccessType.FIELD)
public class SielAnvilRecipe {

	@XmlAttribute(required = true)
	private int id;
	@XmlAttribute(required = true)
	private boolean enabled;
	@XmlAttribute(name = "disabled_reason")
	private String disabledReason;
	@XmlAttribute(name = "ceiling_max_point")
	private int ceilingMax;
	@XmlAttribute(name = "failure_ceiling_point_min")
	private int ceilingMinGain;
	@XmlAttribute(name = "failure_ceiling_point_max")
	private int ceilingMaxGain;
	@XmlElement(name = "product")
	private List<Product> products = new ArrayList<>();
	@XmlElement(name = "refund")
	private List<Ingredient> refunds = new ArrayList<>();
	@XmlElement(name = "materials")
	private List<Materials> materials = new ArrayList<>();

	public int getId() { return id; }
	public boolean isEnabled() { return enabled; }
	public List<Product> getProducts() { return products; }
	public List<Ingredient> getRefunds() { return refunds; }
	public List<Materials> getMaterials() { return materials; }
	public int getCeilingMax() { return ceilingMax; }
	public int getCeilingMinGain() { return ceilingMinGain; }
	public int getCeilingMaxGain() { return ceilingMaxGain; }
	public int nextCeiling(int current, boolean success, int gain) {
		if (success || ceilingMax == 0) return 0;
		if (gain < ceilingMinGain || gain > ceilingMaxGain) throw new IllegalArgumentException("Invalid ceiling gain");
		return Math.min(ceilingMax, current + gain);
	}

	public Materials match(Map<Integer, Long> supplied) {
		return materials.stream().filter(group -> group.asMap().equals(supplied)).findFirst().orElse(null);
	}

	/** Null is the failure outcome, with the remaining probability. */
	public Product selectProduct(int roll) {
		if (roll < 0 || roll >= 10000)
			throw new IllegalArgumentException("Roll must be in [0, 10000)");
		for (Product product : products) {
			if (roll < product.probability)
				return product;
			roll -= product.probability;
		}
		return null;
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Ingredient {
		@XmlAttribute
		private boolean selected;
		@XmlAttribute(name = "item_id", required = true)
		private int itemId;
		@XmlAttribute(required = true)
		private long count;
		public int getItemId() { return itemId; }
		public long getCount() { return count; }
		public boolean isSelected() { return selected; }
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Product extends Ingredient {
		@XmlAttribute(required = true)
		private int index;
		@XmlAttribute(required = true)
		private int probability;
		public int getIndex() { return index; }
		public int getProbability() { return probability; }
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Materials {
		@XmlElement(name = "item")
		private List<Ingredient> items = new ArrayList<>();
		public List<Ingredient> getItems() { return items; }
		public Map<Integer, Long> asMap() {
			Map<Integer, Long> result = new LinkedHashMap<>();
			for (Ingredient item : items)
				result.merge(item.itemId, item.count, Math::addExact);
			return result;
		}
	}
}
