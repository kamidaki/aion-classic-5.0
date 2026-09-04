package com.aionemu.commons.network;

import com.aionemu.commons.network.DisconnectionTask;

public interface DisconnectionThreadPool {
    public void scheduleDisconnection(DisconnectionTask var1, long var2);

    public void waitForDisconnectionTasks();
}

