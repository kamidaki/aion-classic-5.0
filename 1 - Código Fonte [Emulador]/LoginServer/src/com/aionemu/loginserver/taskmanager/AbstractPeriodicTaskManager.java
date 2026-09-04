package com.aionemu.loginserver.taskmanager;

import com.aionemu.commons.taskmanager.AbstractLockManager;
import com.aionemu.loginserver.utils.ThreadPoolManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public abstract class AbstractPeriodicTaskManager extends AbstractLockManager implements Runnable {

    protected static final Logger log = LoggerFactory.getLogger(AbstractPeriodicTaskManager.class);

    private final int period;

    public AbstractPeriodicTaskManager(int period) {
        this.period = period;
        log.info(getClass().getSimpleName() + ": Initialized.");
        ThreadPoolManager.getInstance().scheduleAtFixedRate(this, 1000, period);
    }

    @Override
    public abstract void run();
}
