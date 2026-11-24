package com.aionemu.gameserver.dataholders;

import com.aionemu.gameserver.model.templates.battle_pass.BattlePassSeasonTemplate;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@XmlRootElement(name = "battlepass_seasons")
@XmlAccessorType(XmlAccessType.FIELD)
public class BattlePassSeasonData {

	@XmlElement(name = "battlepass_season")
	private List<BattlePassSeasonTemplate> bplist;

	private Map<Integer, BattlePassSeasonTemplate> seasons = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		for (BattlePassSeasonTemplate seasonTemplate : bplist) {
			seasons.put(seasonTemplate.getId(), seasonTemplate);
		}
	}

	public int size() {
		return seasons.size();
	}

	public BattlePassSeasonTemplate getSeasonById(int id) {
		return seasons.get(id);
	}

	public List<BattlePassSeasonTemplate> getAllTemplate() {
		return bplist;
	}
}
