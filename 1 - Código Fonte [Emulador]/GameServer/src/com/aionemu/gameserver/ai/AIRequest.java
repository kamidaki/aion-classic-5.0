package com.aionemu.gameserver.ai;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;

public abstract class AIRequest {

	public abstract void acceptRequest(Creature requester, Player responder);

	public void acceptRequest(Creature requester, Player responder, int requestId) {
		acceptRequest(requester, responder);
	}

	public void denyRequest(Creature requester, Player responder) {
	}
}
