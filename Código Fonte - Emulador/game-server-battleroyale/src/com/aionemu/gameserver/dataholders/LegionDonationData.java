package com.aionemu.gameserver.dataholders;

import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.Race;

/**
 * Produção de moedas pessoais da Legion (legion/legion_donation.xml, gerado do PC/client_guild_donation.xml).
 * <p>
 * A lista do dia tem um índice de cada grupo que vale para a raça da Legion; produzir consome {@code count} do item, soma {@code points} aos
 * pontos de produção e dá {@code coins} moedas.
 */
@XmlRootElement(name = "legion_donation")
@XmlAccessorType(XmlAccessType.FIELD)
public class LegionDonationData {

	@XmlAttribute(name = "reset_time", required = true)
	private String resetTimeText;

	@XmlElement(name = "group", required = true)
	private List<Group> groups = new ArrayList<>();

	@XmlTransient
	private LocalTime resetTime;

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		resetTime = LocalTime.parse(resetTimeText);
		for (Group group : groups)
			for (int i = 0; i < group.entries.size(); i++)
				if (group.entries.get(i).index != i + 1)
					throw new IllegalArgumentException("Legion donation group " + group.id + ": indexes must start at 1 without gaps");
		groups = List.copyOf(groups);
	}

	public LocalTime getResetTime() {
		return resetTime;
	}

	/**
	 * @return os grupos da lista do dia de uma Legion dessa raça, na ordem do XML
	 */
	public List<Group> getGroups(Race race) {
		return groups.stream().filter(g -> g.race.matches(race)).toList();
	}

	public Group getGroup(int groupId) {
		return groups.stream().filter(g -> g.id == groupId).findFirst().orElse(null);
	}

	public int size() {
		return groups.size();
	}

	@XmlType(name = "LegionDonationRace")
	public enum GroupRace {
		ALL,
		ELYOS,
		ASMODIANS;

		boolean matches(Race race) {
			return this == ALL || name().equals(race.name());
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionDonationGroup")
	public static class Group {

		@XmlAttribute(required = true)
		private int id;

		@XmlAttribute(required = true)
		private String name;

		@XmlAttribute(required = true)
		private GroupRace race;

		@XmlElement(name = "entry", required = true)
		private List<Entry> entries = new ArrayList<>();

		public int getId() {
			return id;
		}

		public String getName() {
			return name;
		}

		public int size() {
			return entries.size();
		}

		/**
		 * @return a entrada do índice (de 1 a {@link #size()}), ou null
		 */
		public Entry getEntry(int index) {
			return index >= 1 && index <= entries.size() ? entries.get(index - 1) : null;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionDonationEntry")
	public static class Entry {

		@XmlAttribute(required = true)
		private int index;

		@XmlAttribute(name = "item_id", required = true)
		private int itemId;

		@XmlAttribute(required = true)
		private int count;

		@XmlAttribute(required = true)
		private int points;

		@XmlAttribute(required = true)
		private int coins;

		public int getIndex() {
			return index;
		}

		public int getItemId() {
			return itemId;
		}

		public int getCount() {
			return count;
		}

		public int getPoints() {
			return points;
		}

		public int getCoins() {
			return coins;
		}
	}
}
