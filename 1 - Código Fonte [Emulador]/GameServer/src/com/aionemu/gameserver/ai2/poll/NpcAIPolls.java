package com.aionemu.gameserver.ai2.poll;

import com.aionemu.gameserver.ai2.NpcAI;


public class NpcAIPolls {

	/**
	 * @param npcAI
	 */
	public static AIAnswer shouldDecay(NpcAI npcAI) {
		return AIAnswers.POSITIVE;
	}

	/**
	 * @param npcAI
	 * @return
	 */
	public static AIAnswer shouldRespawn(NpcAI npcAI) {
		return AIAnswers.POSITIVE;
	}

}
