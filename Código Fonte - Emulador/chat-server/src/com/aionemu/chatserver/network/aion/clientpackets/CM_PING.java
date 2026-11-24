package com.aionemu.chatserver.network.aion.clientpackets;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.network.aion.AbstractClientPacket;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_PING extends AbstractClientPacket {

	public CM_PING(ByteBuf channelBuffer, ClientChannelHandler clientChannelHandler, byte opCode) {
		super(channelBuffer, clientChannelHandler, opCode);
	}

	@Override
	protected void readImpl() {
		readC(); // 0
		readH(); // 0
		readB(16); // 0
	}

	@Override
	protected void runImpl() {
	}
}
