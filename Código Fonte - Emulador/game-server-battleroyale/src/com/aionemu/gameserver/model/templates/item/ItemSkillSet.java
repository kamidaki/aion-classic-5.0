package com.aionemu.gameserver.model.templates.item;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.commons.utils.Rnd;

/**
 * Conjunto de skills de equipamento (client_item_skill_enchant.xml): o item com este skill_set_name ganha uma delas ao ser obtido
 * ("Assign Skill on Loot"), e o Reassign sorteia de novo. prob por mil.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ItemSkillSet")
public class ItemSkillSet {

	@XmlAttribute(required = true)
	private String name;
	@XmlAttribute(required = true)
	private int quna;
	@XmlList
	@XmlElement(required = true)
	private List<Integer> items;
	@XmlElement(name = "skill", required = true)
	private List<ItemSkillSetSkill> skills;

	public String getName() {
		return name;
	}

	/**
	 * @return custo do Reassign em Quna (client_item_skill_enchant_cost, tipo 0)
	 */
	public int getQuna() {
		return quna;
	}

	public List<Integer> getItems() {
		return items;
	}

	public List<ItemSkillSetSkill> getSkills() {
		return skills;
	}

	public boolean contains(int skillId) {
		return skills.stream().anyMatch(s -> s.getId() == skillId);
	}

	/**
	 * Sorteio pelo peso de cada skill (soma 1000 no cliente; menor quando uma skill do conjunto não existe).
	 */
	public int roll() {
		int total = skills.stream().mapToInt(ItemSkillSetSkill::getProb).sum();
		int r = Rnd.nextInt(total);
		for (ItemSkillSetSkill skill : skills) {
			r -= skill.getProb();
			if (r < 0)
				return skill.getId();
		}
		return skills.get(skills.size() - 1).getId();
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "ItemSkillSetSkill")
	public static class ItemSkillSetSkill {

		@XmlAttribute(required = true)
		private int id;
		@XmlAttribute(required = true)
		private int prob;

		public int getId() {
			return id;
		}

		public int getProb() {
			return prob;
		}
	}
}
