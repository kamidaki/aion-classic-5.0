package com.aionemu.gameserver.dataholders;

import com.aionemu.gameserver.questEngine.handlers.models.XMLQuest;

import javax.xml.bind.annotation.*;
import java.util.List;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlRootElement(name = "quest_scripts")
public class XMLQuests
{
	@XmlElements({ @XmlElement(name = "report_to", type = com.aionemu.gameserver.questEngine.handlers.models.ReportToData.class),
	@XmlElement(name = "monster_hunt", type = com.aionemu.gameserver.questEngine.handlers.models.MonsterHuntData.class),
	@XmlElement(name = "xml_quest", type = com.aionemu.gameserver.questEngine.handlers.models.XmlQuestData.class),
	@XmlElement(name = "item_collecting", type = com.aionemu.gameserver.questEngine.handlers.models.ItemCollectingData.class),
	@XmlElement(name = "relic_rewards", type = com.aionemu.gameserver.questEngine.handlers.models.RelicRewardsData.class),
	@XmlElement(name = "crafting_rewards", type = com.aionemu.gameserver.questEngine.handlers.models.CraftingRewardsData.class),
	@XmlElement(name = "report_to_many", type = com.aionemu.gameserver.questEngine.handlers.models.ReportToManyData.class),
	@XmlElement(name = "kill_in_world", type = com.aionemu.gameserver.questEngine.handlers.models.KillInWorldData.class),
	@XmlElement(name = "kill_spawned", type = com.aionemu.gameserver.questEngine.handlers.models.KillSpawnedData.class),
	@XmlElement(name = "mentor_monster_hunt", type = com.aionemu.gameserver.questEngine.handlers.models.MentorMonsterHuntData.class),
	@XmlElement(name = "fountain_rewards", type = com.aionemu.gameserver.questEngine.handlers.models.FountainRewardsData.class),
	@XmlElement(name = "item_order", type = com.aionemu.gameserver.questEngine.handlers.models.ItemOrdersData.class),
	@XmlElement(name = "work_order", type = com.aionemu.gameserver.questEngine.handlers.models.WorkOrdersData.class) })
	protected List<XMLQuest> data;
	
	public List<XMLQuest> getQuest() {
		return data;
	}
	
	public void setData(List<XMLQuest> data) {
		this.data = data;
	}
}