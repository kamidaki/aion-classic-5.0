package com.aionemu.commons.network;

import com.aionemu.commons.network.Dispatcher;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.SelectionKey;
import java.nio.channels.SocketChannel;

public abstract class AConnection {
    private final SocketChannel socketChannel;
    private final Dispatcher dispatcher;
    private SelectionKey key;
    protected boolean pendingClose;
    protected boolean isForcedClosing;
    protected boolean closed;
    protected final Object guard = new Object();
    public final ByteBuffer writeBuffer;
    public final ByteBuffer readBuffer;
    private final String ip;
    private boolean locked = false;

    public AConnection(SocketChannel sc, Dispatcher d, int rbSize, int wbSize) throws IOException {
        this.socketChannel = sc;
        this.dispatcher = d;
        this.writeBuffer = ByteBuffer.allocate(wbSize);
        this.writeBuffer.flip();
        this.writeBuffer.order(ByteOrder.LITTLE_ENDIAN);
        this.readBuffer = ByteBuffer.allocate(rbSize);
        this.readBuffer.order(ByteOrder.LITTLE_ENDIAN);
        this.ip = this.socketChannel.socket().getInetAddress().getHostAddress();
    }

    final void setKey(SelectionKey key) {
        this.key = key;
    }

    protected final void enableWriteInterest() {
        if (this.key.isValid()) {
            this.key.interestOps(this.key.interestOps() | 4);
            this.key.selector().wakeup();
        }
    }

    final Dispatcher getDispatcher() {
        return this.dispatcher;
    }

    public SocketChannel getSocketChannel() {
        return this.socketChannel;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public final void close(boolean forced) {
        Object object = this.guard;
        synchronized (object) {
            if (this.isWriteDisabled()) {
                return;
            }
            this.isForcedClosing = forced;
            this.getDispatcher().closeConnection(this);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    final boolean onlyClose() {
        Object object = this.guard;
        synchronized (object) {
            if (this.closed) {
                return false;
            }
            try {
                if (this.socketChannel.isOpen()) {
                    this.socketChannel.close();
                    this.key.attach(null);
                    this.key.cancel();
                }
                this.closed = true;
            }
            catch (IOException iOException) {
                // empty catch block
            }
        }
        return true;
    }

    final boolean isPendingClose() {
        return this.pendingClose && !this.closed;
    }

    protected final boolean isWriteDisabled() {
        return this.pendingClose || this.closed;
    }

    public final String getIP() {
        return this.ip;
    }

    boolean tryLockConnection() {
        if (this.locked) {
            return false;
        }
        this.locked = true;
        return true;
    }

    void unlockConnection() {
        this.locked = false;
    }

    protected abstract boolean processData(ByteBuffer var1);

    protected abstract boolean writeData(ByteBuffer var1);

    protected abstract void initialized();

    protected abstract long getDisconnectionDelay();

    protected abstract void onDisconnect();

    protected abstract void onServerClose();
}

