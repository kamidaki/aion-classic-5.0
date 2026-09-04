package com.aionemu.commons.network;

import com.aionemu.commons.network.AConnection;

public class DisconnectionTask
implements Runnable {
    private AConnection connection;

    public DisconnectionTask(AConnection connection) {
        this.connection = connection;
    }

    @Override
    public void run() {
        this.connection.onDisconnect();
    }
}

