package com.aionemu.commons.network;

import com.aionemu.commons.network.AConnection;
import com.aionemu.commons.network.Acceptor;
import com.aionemu.commons.network.DisconnectionTask;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.SocketChannel;
import java.nio.channels.spi.SelectorProvider;
import java.util.concurrent.Executor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class Dispatcher
extends Thread {
    private static final Logger log = LoggerFactory.getLogger(Dispatcher.class);
    Selector selector;
    private final Executor dcPool;
    private final Object gate = new Object();

    public Dispatcher(String name, Executor dcPool) throws IOException {
        super(name);
        this.selector = SelectorProvider.provider().openSelector();
        this.dcPool = dcPool;
    }

    abstract void closeConnection(AConnection var1);

    abstract void dispatch() throws IOException;

    public final Selector selector() {
        return this.selector;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     * Converted monitor instructions to comments
     * Lifted jumps to return sites
     */
    @Override
    public void run() {
        while (true) {
            try {
                this.dispatch();
                synchronized (this.gate) {
                }
            }
            catch (Exception e) {
                log.error("Dispatcher error! " + e, (Throwable)e);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public final void register(SelectableChannel ch, int ops, AConnection att) throws IOException {
        Object object = this.gate;
        synchronized (object) {
            this.selector.wakeup();
            att.setKey(ch.register(this.selector, ops, att));
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public final SelectionKey register(SelectableChannel ch, int ops, Acceptor att) throws IOException {
        Object object = this.gate;
        synchronized (object) {
            this.selector.wakeup();
            return ch.register(this.selector, ops, att);
        }
    }

    final void accept(SelectionKey key) {
        try {
            ((Acceptor)key.attachment()).accept(key);
        }
        catch (Exception e) {
            log.error("Error while accepting connection: +" + e, (Throwable)e);
        }
    }

    final void read(SelectionKey key) {
        int numRead;
        SocketChannel socketChannel = (SocketChannel)key.channel();
        AConnection con = (AConnection)key.attachment();
        ByteBuffer rb = con.readBuffer;
        try {
            numRead = socketChannel.read(rb);
        }
        catch (IOException e) {
            this.closeConnectionImpl(con);
            return;
        }
        if (numRead == -1) {
            this.closeConnectionImpl(con);
            return;
        }
        if (numRead == 0) {
            return;
        }
        rb.flip();
        while (rb.remaining() > 2 && rb.remaining() >= rb.getShort(rb.position())) {
            if (this.parse(con, rb)) continue;
            this.closeConnectionImpl(con);
            return;
        }
        if (rb.hasRemaining()) {
            con.readBuffer.compact();
        } else {
            rb.clear();
        }
    }

    private boolean parse(AConnection con, ByteBuffer buf) {
        short sz = 0;
        try {
            sz = buf.getShort();
            if (sz > 1) {
                sz = (short)(sz - 2);
            }
            ByteBuffer b = (ByteBuffer)buf.slice().limit(sz);
            b.order(ByteOrder.LITTLE_ENDIAN);
            buf.position(buf.position() + sz);
            return con.processData(b);
        }
        catch (IllegalArgumentException e) {
            log.warn("Error on parsing input from client - account: " + con + " packet size: " + sz + " real size:" + buf.remaining(), (Throwable)e);
            return false;
        }
    }

    final void write(SelectionKey key) {
        ByteBuffer wb;
        AConnection con;
        block9: {
            int numWrite;
            SocketChannel socketChannel = (SocketChannel)key.channel();
            con = (AConnection)key.attachment();
            wb = con.writeBuffer;
            if (wb.hasRemaining()) {
                try {
                    numWrite = socketChannel.write(wb);
                }
                catch (IOException e) {
                    this.closeConnectionImpl(con);
                    return;
                }
                if (numWrite == 0) {
                    return;
                }
                if (wb.hasRemaining()) {
                    return;
                }
            }
            do {
                boolean writeFailed;
                wb.clear();
                boolean bl = writeFailed = !con.writeData(wb);
                if (writeFailed) break block9;
                try {
                    numWrite = socketChannel.write(wb);
                }
                catch (IOException e) {
                    this.closeConnectionImpl(con);
                    return;
                }
                if (numWrite != 0) continue;
                return;
            } while (!wb.hasRemaining());
            return;
        }
        wb.limit(0);
        key.interestOps(key.interestOps() & 0xFFFFFFFB);
        if (con.isPendingClose()) {
            this.closeConnectionImpl(con);
        }
    }

    protected final void closeConnectionImpl(AConnection con) {
        if (con.onlyClose()) {
            this.dcPool.execute(new DisconnectionTask(con));
        }
    }
}

