package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;
import javax.xml.bind.annotation.XmlType;
import javax.xml.bind.annotation.XmlValue;

/**
 * Moreth, Chronicle of Time (moros/moros.xml, gerado do client_moros_setting.xml e do client_moros_point.xml).
 * <p>
 * Níveis de 1 ao máximo, sem buraco: {@code points} é o que falta para chegar ao nível (o contador zera a cada nível), {@code rate} o valor em %
 * do ponto gravado naquele nível e a passiva do nível. Item fora de toda categoria não pode ser gravado.
 */
@XmlRootElement(name = "moros")
@XmlAccessorType(XmlAccessType.FIELD)
public class MorosData {

	@XmlElement(name = "level", required = true)
	private List<Level> levelList = new ArrayList<>();

	@XmlElement(name = "category")
	private List<Category> categories = new ArrayList<>();

	@XmlTransient
	private List<Level> levels;

	@XmlTransient
	private final Map<Integer, Integer> pointByItemId = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (int i = 0; i < levelList.size(); i++)
			if (levelList.get(i).level != i + 1)
				throw new IllegalArgumentException("Moros levels must start at 1 without gaps, found " + levelList.get(i).level + " at " + i);
		levels = List.copyOf(levelList);
		levelList = null;
		for (Category category : categories)
			for (int itemId : category.itemIds)
				if (pointByItemId.put(itemId, category.point) != null)
					throw new IllegalArgumentException("Item " + itemId + " in more than one Moros category");
		categories = null;
	}

	public int getMaxLevel() {
		return levels.size();
	}

	/**
	 * @return o nível (de 1 a {@link #getMaxLevel()}), ou null
	 */
	public Level getLevel(int level) {
		return level >= 1 && level <= levels.size() ? levels.get(level - 1) : null;
	}

	/**
	 * @return pontos por unidade gravada, ou 0 se o item não pode ser gravado
	 */
	public int getPoint(int itemId) {
		return pointByItemId.getOrDefault(itemId, 0);
	}

	public int size() {
		return pointByItemId.size();
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "MorosLevel")
	public static class Level {

		@XmlAttribute(required = true)
		private int level;

		@XmlAttribute(required = true)
		private long points;

		@XmlAttribute(required = true)
		private int rate;

		@XmlAttribute(name = "skill_id", required = true)
		private int skillId;

		@XmlAttribute(name = "skill_level", required = true)
		private int skillLevel;

		public int getLevel() {
			return level;
		}

		/**
		 * Pontos para chegar a este nível a partir do anterior.
		 */
		public long getPoints() {
			return points;
		}

		/**
		 * Valor do ponto gravado neste nível, em %.
		 */
		public int getRate() {
			return rate;
		}

		public int getSkillId() {
			return skillId;
		}

		public int getSkillLevel() {
			return skillLevel;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "MorosCategory")
	private static class Category {

		@XmlAttribute(required = true)
		private String name;

		@XmlAttribute(required = true)
		private int point;

		@XmlValue
		@XmlList
		private List<Integer> itemIds = new ArrayList<>();
	}
}
