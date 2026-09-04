package com.aionemu.commons.network;

import com.aionemu.commons.network.AConnection;
import com.aionemu.commons.network.ConnectionFactory;
import com.aionemu.commons.network.Dispatcher;
import com.aionemu.commons.network.NioServer;
import java.io.IOException;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SelectionKey;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;

public class Acceptor {
    private final ConnectionFactory factory;
    private final NioServer nioServer;

    Acceptor(ConnectionFactory factory, NioServer nioServer) {
        this.factory = factory;
        this.nioServer = nioServer;
    }

    public final void accept(SelectionKey key) throws IOException {
        ServerSocketChannel serverSocketChannel = (ServerSocketChannel)key.channel();
        SocketChannel socketChannel = serverSocketChannel.accept();
        socketChannel.configureBlocking(false);
        Dispatcher dispatcher = this.nioServer.getReadWriteDispatcher();
        AConnection con = this.factory.create(socketChannel, dispatcher);
        if (con == null) {
            return;
        }
        dispatcher.register((SelectableChannel)socketChannel, 1, con);
        con.initialized();
    }
}

