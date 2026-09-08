package com.aionemu.gameserver.taskmanager;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class AbstractPeriodicTaskManager {

	protected static final Logger log = LoggerFactory.getLogger(AbstractPeriodicTaskManager.class);

	public AbstractPeriodicTaskManager(int period) {
		log.info(getClass().getSimpleName() + " initialized.");
		ThreadPoolManager.getInstance().scheduleAtFixedRate(this::run, Rnd.get(500, 550), period);
	}

	protected abstract void run();
}
