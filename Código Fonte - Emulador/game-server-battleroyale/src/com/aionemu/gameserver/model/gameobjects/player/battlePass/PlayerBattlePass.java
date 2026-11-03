package com.aionemu.gameserver.model.gameobjects.player.battlePass;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class PlayerBattlePass {

	private Map<Integer, BattlePassSeason> battlePassSeason;
	private Map<Integer, BattlePassQuest> battlePassQuest;

	public PlayerBattlePass() {
		this.battlePassSeason = new ConcurrentHashMap<>();
		this.battlePassQuest = new ConcurrentHashMap<>();
	}

	public Map<Integer, BattlePassSeason> getBattlePassSeason() {
		return battlePassSeason;
	}

	public void setBattlePassSeason(Map<Integer, BattlePassSeason> battlePassSeason) {
		this.battlePassSeason = battlePassSeason;
	}

	public Map<Integer, BattlePassQuest> getBattlePassQuest() {
		return battlePassQuest;
	}

	public void setBattlePassQuest(Map<Integer, BattlePassQuest> battlePassQuest) {
		this.battlePassQuest = battlePassQuest;
	}

	public boolean haveQuest(int questId) {
		for (BattlePassQuest quest : this.battlePassQuest.values()) {
			if (quest.getId() == questId) {
				return true;
			}
		}
		return false;
	}
}
