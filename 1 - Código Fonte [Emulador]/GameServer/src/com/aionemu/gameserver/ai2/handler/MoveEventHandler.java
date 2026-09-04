package com.aionemu.gameserver.ai2.handler;

import com.aionemu.gameserver.ai2.NpcAI;
import com.aionemu.gameserver.ai2.handler.TargetEventHandler;

public class MoveEventHandler
{
	public static void onMoveValidate(NpcAI npcAI) {
        npcAI.getOwner().getController().onMove();
        TargetEventHandler.onTargetTooFar(npcAI);
    }
	
	public static void onMoveArrived(NpcAI npcAI) {
        npcAI.getOwner().getController().onMove();
        TargetEventHandler.onTargetReached(npcAI);
    }
}