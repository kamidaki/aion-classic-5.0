package com.aionemu.commons.network;

import com.aionemu.commons.network.AConnection;
import com.aionemu.commons.network.Dispatcher;
import java.io.IOException;
import java.nio.channels.SocketChannel;

public interface ConnectionFactory {
    public AConnection create(SocketChannel var1, Dispatcher var2) throws IOException;
}

