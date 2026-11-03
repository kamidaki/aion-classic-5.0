package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlType;

/**
 * Nível de crescimento da Legion (legion/legion_growth.xml, gerado do PC/client_guild_growth.xml): exp para chegar a cada nível (o contador
 * zera a cada nível) e o que a Legion ganha ao chegar nele.
 */
@XmlRootElement(name = "legion_growth")
@XmlAccessorType(XmlAccessType.FIELD)
public class LegionGrowthData {

	@XmlElement(name = "level", required = true)
	private List<Level> levels = new ArrayList<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (int i = 0; i < levels.size(); i++)
			if (levels.get(i).level != i + 1)
				throw new IllegalArgumentException("Legion growth levels must start at 1 without gaps, found " + levels.get(i).level + " at " + i);
		levels = List.copyOf(levels);
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

	public int size() {
		return levels.size();
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionGrowthLevel")
	public static class Level {

		@XmlAttribute(required = true)
		private int level;

		@XmlAttribute(required = true)
		private int exp;

		@XmlAttribute(required = true)
		private int essence;

		@XmlAttribute(name = "essence_piece", required = true)
		private int essencePiece;

		public int getExp() {
			return exp;
		}

		public int getEssence() {
			return essence;
		}

		public int getEssencePiece() {
			return essencePiece;
		}
	}
}
