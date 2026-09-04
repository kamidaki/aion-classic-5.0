package com.aionemu.gameserver.ai.scenario;

import com.aionemu.gameserver.ai.AbstractAI;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.model.gameobjects.Creature;


public interface AIScenario {

	void onCreatureEvent(AbstractAI ai, AIEventType event, Creature creature);

	void onGeneralEvent(AbstractAI ai, AIEventType event);
}
