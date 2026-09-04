package com.aionemu.gameserver.ai.poll;

import com.aionemu.gameserver.ai.NpcAI;


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
