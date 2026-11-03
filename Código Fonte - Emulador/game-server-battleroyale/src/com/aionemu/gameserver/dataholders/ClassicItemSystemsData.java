package com.aionemu.gameserver.dataholders;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;

/** Rules imported from the official Classic 5.0 client; no estimated gameplay constants. */
@XmlRootElement(name = "classic_item_systems")
@XmlAccessorType(XmlAccessType.FIELD)
public class ClassicItemSystemsData {

	@XmlElement(name = "enchant")
	private List<EnchantRule> enchants;
	@XmlElement(name = "gap")
	private List<GapRule> gaps;
	@XmlElement(name = "power")
	private List<PowerRule> powers;
	@XmlElement(name = "combat_reward")
	private List<CombatRewardRule> combatRewards;
	@XmlTransient private final Map<String, EnchantRule> enchantByKey = new HashMap<>();
	@XmlTransient private final Map<String, Integer> gapByKey = new HashMap<>();
	@XmlTransient private final Map<String, Integer> powerByKey = new HashMap<>();
	@XmlTransient private final Map<Integer, CombatRewardRule> combatRewardById = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		if (enchants != null)
			for (EnchantRule rule : enchants) enchantByKey.put(rule.group + ":" + rule.before, rule);
		if (gaps != null)
			for (GapRule rule : gaps) gapByKey.put(rule.grade + ":" + rule.level + ":" + rule.quality, rule.probability);
		if (powers != null)
			for (PowerRule rule : powers) powerByKey.put(rule.type + ":" + rule.value.toLowerCase(java.util.Locale.ROOT), rule.points);
		if (combatRewards != null)
			for (CombatRewardRule rule : combatRewards) combatRewardById.put(rule.id, rule);
		 enchants = null; gaps = null; powers = null; combatRewards = null;
	}

	public EnchantRule getEnchant(String group, int level) { return enchantByKey.get(group + ":" + level); }
	public Integer getGap(int grade, int level, String quality) { return gapByKey.get(grade + ":" + level + ":" + quality); }
	public int getPower(String type, String value) { return powerByKey.getOrDefault(type + ":" + value.toLowerCase(java.util.Locale.ROOT), 0); }
	public CombatRewardRule getCombatReward(int id) { return combatRewardById.get(id); }
	public int getCombatRewardCount() { return combatRewardById.size(); }
	public int size() { return enchantByKey.size() + gapByKey.size() + powerByKey.size() + combatRewardById.size(); }

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class EnchantRule {
		@XmlAttribute public String group;
		@XmlAttribute public int before;
		@XmlAttribute public int success;
		@XmlAttribute public int failure;
		@XmlAttribute public int probability;
		@XmlAttribute public int stones;
		@XmlAttribute public int component;
		@XmlAttribute public long cost;
	}
	@XmlAccessorType(XmlAccessType.FIELD)
	public static class GapRule {
		@XmlAttribute public int grade;
		@XmlAttribute public int level;
		@XmlAttribute public String quality;
		@XmlAttribute public int probability;
	}
	@XmlAccessorType(XmlAccessType.FIELD)
	public static class PowerRule {
		@XmlAttribute public String type;
		@XmlAttribute public String value;
		@XmlAttribute public int points;
	}
	@XmlAccessorType(XmlAccessType.FIELD)
	public static class CombatRewardRule {
		@XmlAttribute public int id;
		@XmlAttribute public int goal;
		@XmlAttribute public int item;
		@XmlAttribute public long amount;
	}
}
