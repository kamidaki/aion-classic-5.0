package com.aionemu.gameserver.model.templates.item;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * Receita do Ascend (client_item_upgrade.xml): troca o item de origem, com encantamento entre {@code enchant_min} e {@code enchant_max}, pelo
 * resultado sorteado de uma das opções. A opção é escolhida pelo cliente (índice no C 0x106) e tem o custo e as faixas FAIL/UP/TOP, com chance em
 * 1/10000.
 */
@XmlAccessorType(XmlAccessType.FIELD)
public class ItemUpgradeTemplate {

	@XmlType(name = "ItemUpgradeGrade")
	@XmlEnum
	public enum Grade {
		FAIL,
		UP,
		TOP
	}

	@XmlAttribute(required = true)
	private int id;

	@XmlAttribute(required = true)
	private String name;

	@XmlAttribute(name = "item_id", required = true)
	private int itemId;

	@XmlAttribute(name = "enchant_min", required = true)
	private int enchantMin;

	@XmlAttribute(name = "enchant_max", required = true)
	private int enchantMax;

	@XmlAttribute(name = "skill_transfer", required = true)
	private boolean skillTransfer;

	@XmlAttribute(name = "option_transfer", required = true)
	private boolean optionTransfer;

	@XmlAttribute(name = "proc_transfer", required = true)
	private boolean procTransfer;

	@XmlAttribute(name = "gemstone_transfer", required = true)
	private boolean gemstoneTransfer;

	@XmlElement(name = "option", required = true)
	private List<Option> options = new ArrayList<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		options = List.copyOf(options);
	}

	public int getId() {
		return id;
	}

	public String getName() {
		return name;
	}

	public int getItemId() {
		return itemId;
	}

	public int getEnchantMin() {
		return enchantMin;
	}

	public int getEnchantMax() {
		return enchantMax;
	}

	/**
	 * A skill do item (buff skill) passa para o resultado.
	 */
	public boolean isSkillTransfer() {
		return skillTransfer;
	}

	/**
	 * As manastones passam para o resultado.
	 */
	public boolean isOptionTransfer() {
		return optionTransfer;
	}

	/**
	 * A godstone passa para o resultado.
	 */
	public boolean isProcTransfer() {
		return procTransfer;
	}

	/**
	 * new_gemstone_transfer do cliente; o emulador não tem a new gemstone, então nada é copiado por essa marca.
	 */
	public boolean isGemstoneTransfer() {
		return gemstoneTransfer;
	}

	public List<Option> getOptions() {
		return options;
	}

	/**
	 * @return a opção do índice mandado pelo cliente, ou null
	 */
	public Option getOption(int index) {
		return index >= 0 && index < options.size() ? options.get(index) : null;
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "ItemUpgradeOption")
	public static class Option {

		@XmlAttribute(required = true)
		private long kinah;

		@XmlAttribute(required = true)
		private int ap;

		@XmlElement(name = "material")
		private List<Material> materials = new ArrayList<>();

		@XmlElement(name = "result", required = true)
		private List<Result> results = new ArrayList<>();

		void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
			materials = List.copyOf(materials);
			results = List.copyOf(results);
		}

		public long getKinah() {
			return kinah;
		}

		public int getAp() {
			return ap;
		}

		public List<Material> getMaterials() {
			return materials;
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
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "ItemUpgradeMaterial")
	public static class Material {

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
	@XmlType(name = "ItemUpgradeResult")
	public static class Result {

		@XmlAttribute(required = true)
		private Grade grade;

		@XmlAttribute(required = true)
		private int rate;

		@XmlAttribute(name = "item_id", required = true)
		private int itemId;

		@XmlAttribute(required = true)
		private long count;

		@XmlAttribute(required = true)
		private int enchant;

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

		/**
		 * Encantamento com que o item novo nasce.
		 */
		public int getEnchant() {
			return enchant;
		}
	}
}
