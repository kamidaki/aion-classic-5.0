package com.aionemu.gameserver.dataholders;

import com.aionemu.gameserver.model.templates.battle_pass.BattlePassQuestTemplate;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@XmlRootElement(name = "battlepass_quests")
@XmlAccessorType(XmlAccessType.FIELD)
public class BattlePassQuestData {

	@XmlElement(name = "battlepass_quest")
	private List<BattlePassQuestTemplate> bplist;

	private Map<Integer, BattlePassQuestTemplate> quests = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		for (BattlePassQuestTemplate questTemplate : bplist) {
			quests.put(questTemplate.getId(), questTemplate);
		}
	}

	public int size() {
		return quests.size();
	}

	public BattlePassQuestTemplate getQuestById(int id) {
		return quests.get(id);
	}

	public List<BattlePassQuestTemplate> getAllTemplate() {
		return bplist;
	}
}
