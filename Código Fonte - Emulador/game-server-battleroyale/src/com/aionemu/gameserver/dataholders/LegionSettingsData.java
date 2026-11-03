package com.aionemu.gameserver.dataholders;

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

/**
 * Níveis da Legion (legion/legion_settings.xml, gerado do guild/client_guild_setting.xml do cliente 5.0).
 * <p>
 * Níveis de 1 ao máximo, sem buraco. {@code kinah}, {@code required_members} e {@code required_contribution} são o que se exige para chegar ao
 * nível (o nível 1 é a criação); {@code max_members} e {@code warehouse_slots} valem enquanto a Legion está nele.
 */
@XmlRootElement(name = "legion_settings")
@XmlAccessorType(XmlAccessType.FIELD)
public class LegionSettingsData {

	@XmlElement(name = "level", required = true)
	private List<Level> levelList = new ArrayList<>();

	@XmlTransient
	private List<Level> levels;

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (int i = 0; i < levelList.size(); i++)
			if (levelList.get(i).level != i + 1)
				throw new IllegalArgumentException("Legion levels must start at 1 without gaps, found " + levelList.get(i).level + " at " + i);
		levels = List.copyOf(levelList);
		levelList = null;
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
	@XmlType(name = "LegionSettingsLevel")
	public static class Level {

		@XmlAttribute(required = true)
		private int level;

		@XmlAttribute(required = true)
		private long kinah;

		@XmlAttribute(name = "required_members", required = true)
		private int requiredMembers;

		@XmlAttribute(name = "required_contribution", required = true)
		private long requiredContribution;

		@XmlAttribute(name = "max_members", required = true)
		private int maxMembers;

		@XmlAttribute(name = "warehouse_slots", required = true)
		private int warehouseSlots;

		@XmlAttribute(name = "warehouse_deposit_kinah", required = true)
		private long warehouseDepositKinah;

		@XmlAttribute(name = "warehouse_withdraw_kinah", required = true)
		private long warehouseWithdrawKinah;

		public int getLevel() {
			return level;
		}

		public long getKinah() {
			return kinah;
		}

		public int getRequiredMembers() {
			return requiredMembers;
		}

		public long getRequiredContribution() {
			return requiredContribution;
		}

		public int getMaxMembers() {
			return maxMembers;
		}

		public int getWarehouseSlots() {
			return warehouseSlots;
		}

		public long getWarehouseDepositKinah() {
			return warehouseDepositKinah;
		}

		public long getWarehouseWithdrawKinah() {
			return warehouseWithdrawKinah;
		}
	}
}
