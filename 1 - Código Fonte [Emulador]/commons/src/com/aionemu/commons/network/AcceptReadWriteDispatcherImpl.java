package com.aionemu.commons.network;

import com.aionemu.commons.network.AConnection;
import com.aionemu.commons.network.Dispatcher;
import java.io.IOException;
import java.nio.channels.SelectionKey;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.Executor;

public class AcceptReadWriteDispatcherImpl
extends Dispatcher {
    private final List<AConnection> pendingClose = new ArrayList<AConnection>();

    public AcceptReadWriteDispatcherImpl(String name, Executor dcPool) throws IOException {
        super(name, dcPool);
    }

    @Override
    void dispatch() throws IOException {
        int selected = this.selector.select();
        this.processPendingClose();
        if (selected != 0) {
            Iterator<SelectionKey> selectedKeys = this.selector.selectedKeys().iterator();
            while (selectedKeys.hasNext()) {
                SelectionKey key = selectedKeys.next();
                selectedKeys.remove();
                if (!key.isValid()) continue;
                switch (key.readyOps()) {
                    case 16: {
                        this.accept(key);
                        break;
                    }
                    case 1: {
                        this.read(key);
                        break;
                    }
                    case 4: {
                        this.write(key);
                        break;
                    }
                    case 5: {
                        this.read(key);
                        if (!key.isValid()) break;
                        this.write(key);
                    }
                }
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    void closeConnection(AConnection con) {
        List<AConnection> list = this.pendingClose;
        synchronized (list) {
            this.pendingClose.add(con);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void processPendingClose() {
        List<AConnection> list = this.pendingClose;
        synchronized (list) {
            for (AConnection connection : this.pendingClose) {
                this.closeConnectionImpl(connection);
            }
            this.pendingClose.clear();
        }
    }
}

