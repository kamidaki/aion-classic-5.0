package com.aionemu.gameserver.questEngine.handlers.models;

import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.handlers.template.KillSpawned;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "KillSpawnedData")
public class KillSpawnedData extends MonsterHuntData
{
	@XmlElement(name = "spawned_monster", required = true)
	protected List<SpawnedMonster> spawnedMonster;
	
	@Override
	public void register(QuestEngine questEngine) {
		Map<List<Integer>, SpawnedMonster> spawnedMonsters = new HashMap<List<Integer>, SpawnedMonster>();
		for (SpawnedMonster m : spawnedMonster) {
			spawnedMonsters.put(m.getNpcIds(), m);
		}
		KillSpawned template = new KillSpawned(id, startNpcIds, endNpcIds, spawnedMonsters);
		questEngine.addQuestHandler(template);
	}
}