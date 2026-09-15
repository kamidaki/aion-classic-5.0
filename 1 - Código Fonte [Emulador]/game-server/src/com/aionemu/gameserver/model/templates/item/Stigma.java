package com.aionemu.gameserver.model.templates.item;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

/**
 * Classic 5.0 stigma stone, generated from client_items by fix_50_stigma.py. It teaches exactly its gain skills (not the whole skill group
 * as in 4.8) and, for greater stigmas, requires one skill of each required group to be active on the stigma page.
 *
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.NONE)
@XmlRootElement(name = "Stigma")
public class Stigma {

	public enum StigmaKind {
		NORMAL, // any slot
		GREATER, // greater stigma slots only
		META // any slot, no required skills
	}

	public record StigmaSkill(int skillId, int level) {}

	public record RequiredSkillGroup(List<Integer> skillIds, int level) {}

	@XmlAttribute(name = "kind", required = true)
	private StigmaKind kind;

	@XmlAttribute(name = "shard")
	private int shard;

	@XmlAttribute(name = "gain_skill1")
	private int gainSkill1;

	@XmlAttribute(name = "gain_level1")
	private int gainLevel1 = 1;

	@XmlAttribute(name = "gain_skill2")
	private int gainSkill2;

	@XmlAttribute(name = "gain_level2")
	private int gainLevel2 = 1;

	@XmlAttribute(name = "require_skill1")
	private List<Integer> requireSkill1;

	@XmlAttribute(name = "require_skill1_lv")
	private int requireSkill1Level = 1;

	@XmlAttribute(name = "require_skill2")
	private List<Integer> requireSkill2;

	@XmlAttribute(name = "require_skill2_lv")
	private int requireSkill2Level = 1;

	@XmlAttribute(name = "chargeable")
	private boolean chargeable;

	@XmlTransient
	private List<StigmaSkill> gainSkills;

	@XmlTransient
	private List<RequiredSkillGroup> requiredSkillGroups;

	void afterUnmarshal(Unmarshaller u, Object parent) {
		List<StigmaSkill> gain = new ArrayList<>(2);
		if (gainSkill1 != 0)
			gain.add(new StigmaSkill(gainSkill1, gainLevel1));
		if (gainSkill2 != 0)
			gain.add(new StigmaSkill(gainSkill2, gainLevel2));
		gainSkills = List.copyOf(gain);

		List<RequiredSkillGroup> groups = new ArrayList<>(2);
		if (requireSkill1 != null && !requireSkill1.isEmpty())
			groups.add(new RequiredSkillGroup(List.copyOf(requireSkill1), requireSkill1Level));
		if (requireSkill2 != null && !requireSkill2.isEmpty())
			groups.add(new RequiredSkillGroup(List.copyOf(requireSkill2), requireSkill2Level));
		requiredSkillGroups = List.copyOf(groups);
	}

	public StigmaKind getKind() {
		return kind;
	}

	/**
	 * @return Stigma shards consumed to equip this stone (client require_shard).
	 */
	public int getShard() {
		return shard;
	}

	public List<StigmaSkill> getGainSkills() {
		return gainSkills;
	}

	public boolean grantsSkill(int skillId) {
		return gainSkills.stream().anyMatch(s -> s.skillId() == skillId);
	}

	public List<RequiredSkillGroup> getRequiredSkillGroups() {
		return requiredSkillGroups;
	}

	public boolean isChargeable() {
		return chargeable;
	}
}
