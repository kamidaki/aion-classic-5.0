package com.aionemu.chatserver.network.aion;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.common.netty.BaseServerPacket;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class AbstractServerPacket extends BaseServerPacket {

	public AbstractServerPacket(byte opCode) {
		super(opCode);
	}

	public void write(ClientChannelHandler clientChannelHandler, ByteBuf buf) {
		buf.writeShort((short) 0);
		writeImpl(clientChannelHandler, buf);
	}

	protected abstract void writeImpl(ClientChannelHandler cHandler, ByteBuf buf);
}
