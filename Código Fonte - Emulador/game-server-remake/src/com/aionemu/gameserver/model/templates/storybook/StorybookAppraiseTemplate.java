package com.aionemu.gameserver.model.templates.storybook;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;

/**
 * Identificação de um fragmento desconhecido do Book of Legends (client_appraise_item.xml): cada unidade vira um dos fragmentos da lista, com
 * chance em 1/10000.
 */
@XmlAccessorType(XmlAccessType.FIELD)
public class StorybookAppraiseTemplate {

	@XmlAttribute(name = "item_id", required = true)
	private int itemId;

	@XmlElement(name = "result", required = true)
	private List<Result> results = new ArrayList<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		results = List.copyOf(results);
	}

	public int getItemId() {
		return itemId;
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
	@XmlType(name = "StorybookAppraiseResult")
	public static class Result {

		@XmlAttribute(name = "item_id", required = true)
		private int itemId;

		@XmlAttribute(required = true)
		private long count;

		@XmlAttribute(required = true)
		private int rate;

		public int getItemId() {
			return itemId;
		}

		public long getCount() {
			return count;
		}

		public int getRate() {
			return rate;
		}
	}
}
