package com.aionemu.commons.network;

import com.aionemu.commons.network.AConnection;
import com.aionemu.commons.network.AcceptDispatcherImpl;
import com.aionemu.commons.network.AcceptReadWriteDispatcherImpl;
import com.aionemu.commons.network.Acceptor;
import com.aionemu.commons.network.Dispatcher;
import com.aionemu.commons.network.ServerCfg;
import com.aionemu.commons.network.util.ThreadPoolManager;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SelectionKey;
import java.nio.channels.ServerSocketChannel;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NioServer {
    private static final Logger log = LoggerFactory.getLogger((String)NioServer.class.getName());
    private final List<SelectionKey> serverChannelKeys = new ArrayList<SelectionKey>();
    private Dispatcher acceptDispatcher;
    private int currentReadWriteDispatcher;
    private Dispatcher[] readWriteDispatchers;
    private final Executor dcPool = ThreadPoolManager.getInstance();
    private int readWriteThreads;
    private ServerCfg[] cfgs;

    public NioServer(int readWriteThreads, ServerCfg ... cfgs) {
        this.readWriteThreads = readWriteThreads;
        this.cfgs = cfgs;
    }

    public void connect() {
        try {
            this.initDispatchers(this.readWriteThreads, this.dcPool);
            for (ServerCfg cfg : this.cfgs) {
                InetSocketAddress isa;
                ServerSocketChannel serverChannel = ServerSocketChannel.open();
                serverChannel.configureBlocking(false);
                if ("*".equals(cfg.hostName)) {
                    isa = new InetSocketAddress(cfg.port);
                    log.info("Server listening on all available IPs on Port " + cfg.port + " for " + cfg.connectionName);
                } else {
                    isa = new InetSocketAddress(cfg.hostName, cfg.port);
                    log.info("Server listening on IP: " + cfg.hostName + " Port " + cfg.port + " for " + cfg.connectionName);
                }
                serverChannel.socket().bind(isa);
                SelectionKey acceptKey = this.getAcceptDispatcher().register((SelectableChannel)serverChannel, 16, new Acceptor(cfg.factory, this));
                this.serverChannelKeys.add(acceptKey);
            }
        }
        catch (Exception e) {
            log.error("NioServer Initialization Error: " + e, (Throwable)e);
            throw new Error("NioServer Initialization Error!");
        }
    }

    public final Dispatcher getAcceptDispatcher() {
        return this.acceptDispatcher;
    }

    public final Dispatcher getReadWriteDispatcher() {
        if (this.readWriteDispatchers == null) {
            return this.acceptDispatcher;
        }
        if (this.readWriteDispatchers.length == 1) {
            return this.readWriteDispatchers[0];
        }
        if (this.currentReadWriteDispatcher >= this.readWriteDispatchers.length) {
            this.currentReadWriteDispatcher = 0;
        }
        return this.readWriteDispatchers[this.currentReadWriteDispatcher++];
    }

    private void initDispatchers(int readWriteThreads, Executor dcPool) throws IOException {
        if (readWriteThreads < 1) {
            this.acceptDispatcher = new AcceptReadWriteDispatcherImpl("AcceptReadWrite Dispatcher", dcPool);
            this.acceptDispatcher.start();
        } else {
            this.acceptDispatcher = new AcceptDispatcherImpl("Accept Dispatcher");
            this.acceptDispatcher.start();
            this.readWriteDispatchers = new Dispatcher[readWriteThreads];
            for (int i = 0; i < this.readWriteDispatchers.length; ++i) {
                this.readWriteDispatchers[i] = new AcceptReadWriteDispatcherImpl("ReadWrite-" + i + " Dispatcher", dcPool);
                this.readWriteDispatchers[i].start();
            }
        }
    }

    public final int getActiveConnections() {
        int count = 0;
        if (this.readWriteDispatchers != null) {
            for (Dispatcher d : this.readWriteDispatchers) {
                count += d.selector().keys().size();
            }
        } else {
            count = this.acceptDispatcher.selector().keys().size() - this.serverChannelKeys.size();
        }
        return count;
    }

    public final void shutdown() {
        log.info("Closing ServerChannels...");
        try {
            for (SelectionKey key : this.serverChannelKeys) {
                key.cancel();
            }
            log.info("ServerChannel closed.");
        }
        catch (Exception e) {
            log.error("Error during closing ServerChannel, " + e, (Throwable)e);
        }
        this.notifyServerClose();
        try {
            Thread.sleep(1000L);
        }
        catch (Throwable t) {
            log.warn("Nio thread was interrupted during shutdown", t);
        }
        log.info(" Active connections: " + this.getActiveConnections());
        log.info("Forced Disconnecting all connections...");
        this.closeAll();
        log.info(" Active connections: " + this.getActiveConnections());
        try {
            Thread.sleep(1000L);
        }
        catch (Throwable t) {
            log.warn("Nio thread was interrupted during shutdown", t);
        }
    }

    private void notifyServerClose() {
        if (this.readWriteDispatchers != null) {
            for (Dispatcher d : this.readWriteDispatchers) {
                for (SelectionKey key : d.selector().keys()) {
                    if (!(key.attachment() instanceof AConnection)) continue;
                    ((AConnection)key.attachment()).onServerClose();
                }
            }
        } else {
            for (SelectionKey key : this.acceptDispatcher.selector().keys()) {
                if (!(key.attachment() instanceof AConnection)) continue;
                ((AConnection)key.attachment()).onServerClose();
            }
        }
    }

    private void closeAll() {
        if (this.readWriteDispatchers != null) {
            for (Dispatcher d : this.readWriteDispatchers) {
                for (SelectionKey key : d.selector().keys()) {
                    if (!(key.attachment() instanceof AConnection)) continue;
                    ((AConnection)key.attachment()).close(true);
                }
            }
        } else {
            for (SelectionKey key : this.acceptDispatcher.selector().keys()) {
                if (!(key.attachment() instanceof AConnection)) continue;
                ((AConnection)key.attachment()).close(true);
            }
        }
    }
}

