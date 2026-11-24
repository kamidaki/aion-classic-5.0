package com.aionemu.gameserver.model.templates.storybook;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlTransient;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.stats.ModifiersTemplate;

/**
 * Livro do Book of Legends (client_storybook.xml + client_storybook_reward.xml): os itens que o livro pede, com a quantidade de cada um, e a
 * recompensa ao completar (atributos para sempre, skill ou itens, conforme o tipo).
 */
@XmlAccessorType(XmlAccessType.FIELD)
public class StorybookTemplate {

	@XmlType(name = "StorybookType")
	@XmlEnum
	public enum Type {
		PUZZLE,
		NATURE,
		ADVENTURE
	}

	@XmlAttribute(required = true)
	private int id;

	@XmlAttribute(required = true)
	private String name;

	@XmlAttribute(required = true)
	private Type type;

	@XmlElement(name = "piece", required = true)
	private List<Item> pieceList = new ArrayList<>();

	@XmlElement(name = "modifiers")
	private ModifiersTemplate modifiers;

	@XmlElement(name = "reward_skill")
	private List<Skill> rewardSkills = new ArrayList<>();

	@XmlElement(name = "reward_item")
	private List<Item> rewardItems = new ArrayList<>();

	@XmlTransient
	private Map<Integer, Long> pieces;

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		Map<Integer, Long> map = new LinkedHashMap<>();
		for (Item piece : pieceList)
			if (map.put(piece.itemId, piece.count) != null)
				throw new IllegalArgumentException("Storybook " + id + " repeats item " + piece.itemId);
		pieces = Collections.unmodifiableMap(map);
		pieceList = null;
		rewardSkills = List.copyOf(rewardSkills);
		rewardItems = List.copyOf(rewardItems);
	}

	public int getId() {
		return id;
	}

	public String getName() {
		return name;
	}

	public Type getType() {
		return type;
	}

	/**
	 * itemId -> unidades que o livro pede, na ordem do cliente
	 */
	public Map<Integer, Long> getPieces() {
		return pieces;
	}

	public List<StatFunction> getModifiers() {
		return modifiers == null ? null : modifiers.getModifiers();
	}

	public List<Skill> getRewardSkills() {
		return rewardSkills;
	}

	public List<Item> getRewardItems() {
		return rewardItems;
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "StorybookItem")
	public static class Item {

		@XmlAttribute(name = "item_id", required = true)
		private int itemId;

		@XmlAttribute(required = true)
		private long count;

		public int getItemId() {
			return itemId;
		}

		public long getCount() {
			return count;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "StorybookSkill")
	public static class Skill {

		@XmlAttribute(name = "skill_id", required = true)
		private int skillId;

		@XmlAttribute(required = true)
		private int level;

		public int getSkillId() {
			return skillId;
		}

		public int getLevel() {
			return level;
		}
	}
}
