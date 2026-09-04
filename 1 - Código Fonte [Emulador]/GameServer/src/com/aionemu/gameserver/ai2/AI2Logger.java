package com.aionemu.gameserver.ai2;

import com.aionemu.gameserver.configs.main.AIConfig;
import com.aionemu.gameserver.model.gameobjects.Creature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class AI2Logger {

	private static final Logger log = LoggerFactory.getLogger(AI2Logger.class);

	public static final void info(AbstractAI ai, String message) {
		if (ai.isLogging()) {
			log.info("[AI] " + ai.getOwner().getObjectId() + " - " + message);
		}
	}

	public static final void info(AI ai, String message) {
		info((AbstractAI) ai, message);
	}

	/**
	 * @param owner
	 * @param message
	 */
	public static void moveinfo(Creature owner, String message) {
		if (AIConfig.MOVE_DEBUG && owner.getAi().isLogging()) {
			log.info("[AI] " + owner.getObjectId() + " - " + message);
		}
	}
}
