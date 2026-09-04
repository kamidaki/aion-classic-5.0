package com.aionemu.gameserver.ai.handler;

import com.aionemu.gameserver.ai.AILogger;
import com.aionemu.gameserver.ai.AIState;
import com.aionemu.gameserver.ai.AISubState;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.poll.AIQuestion;
import com.aionemu.gameserver.model.gameobjects.Npc;

public class DiedEventHandler {

	public static void onDie(NpcAI npcAI) {
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "onDie");
		}

		onSimpleDie(npcAI);

		Npc owner = npcAI.getOwner();
		owner.setTarget(null);
	}

	public static void onSimpleDie(NpcAI npcAI) {
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "onSimpleDie");
		}

		if (npcAI.poll(AIQuestion.CAN_SHOUT))
			ShoutEventHandler.onDied(npcAI);

		npcAI.setStateIfNot(AIState.DIED);
		npcAI.setSubStateIfNot(AISubState.NONE);
		npcAI.getOwner().getAggroList().clear();
	}
}
