package com.aionemu.gameserver.model.templates.item;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlTransient;

/**
 * Receita do Altar of Transcendence (client_item_compose.xml): {@code material_count} itens do mesmo grupo e a taxa em kinah por fusão;
 * o resultado sai de uma das faixas SAME/UP/TOP, com chance em 1/10000.
 */
@XmlAccessorType(XmlAccessType.FIELD)
public class ItemComposeRecipe {

	public enum Grade {
		SAME,
		UP,
		TOP
	}

	@XmlAttribute(required = true)
	private int id;

	@XmlAttribute(required = true)
	private String name;

	@XmlAttribute(name = "material_count", required = true)
	private int materialCount;

	@XmlAttribute(required = true)
	private long fee;

	@XmlList
	@XmlElement(name = "materials", required = true)
	private List<Integer> materialList = new ArrayList<>();

	@XmlElement(name = "result", required = true)
	private List<Result> results = new ArrayList<>();

	@XmlTransient
	private final Set<Integer> materials = new HashSet<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		materials.addAll(materialList);
		materialList = null;
		results = List.copyOf(results);
	}

	public int getId() {
		return id;
	}

	public String getName() {
		return name;
	}

	public int getMaterialCount() {
		return materialCount;
	}

	public long getFee() {
		return fee;
	}

	public boolean isMaterial(int itemId) {
		return materials.contains(itemId);
	}

	public boolean hasMaterials() {
		return !materials.isEmpty();
	}

	public List<Result> getResults() {
		return results;
	}

	/**
	 * @param roll
	 *          de 0 a 9999
	 */
	public Result roll(int roll) {
		for (Result result : results) {
			if (roll < result.rate)
				return result;
			roll -= result.rate;
		}
		return results.getLast();
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Result {

		@XmlAttribute(required = true)
		private Grade grade;

		@XmlAttribute(required = true)
		private int rate;

		@XmlAttribute(name = "item_id", required = true)
		private int itemId;

		@XmlAttribute(required = true)
		private long count;

		public Grade getGrade() {
			return grade;
		}

		public int getRate() {
			return rate;
		}

		public int getItemId() {
			return itemId;
		}

		public long getCount() {
			return count;
		}
	}
}
