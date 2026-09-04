package com.aionemu.gameserver.ai2.handler;

import com.aionemu.gameserver.ai2.AIState;
import com.aionemu.gameserver.ai2.NpcAI;

public class SpawnEventHandler
{
	public static void onSpawn(NpcAI npcAI) {
        if (npcAI.setStateIfNot(AIState.IDLE) && npcAI.getOwner().getPosition().isMapRegionActive()) {
            npcAI.think();
        }
    }
	
	public static void onDespawn(NpcAI npcAI) {
		npcAI.setStateIfNot(AIState.DESPAWNED);
	}
	
	public static void onRespawn(NpcAI npcAI) {
		npcAI.getOwner().getMoveController().resetMove();
	}
}