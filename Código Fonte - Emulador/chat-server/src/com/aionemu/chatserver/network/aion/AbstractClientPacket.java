package com.aionemu.chatserver.network.aion;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.common.netty.BaseClientPacket;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class AbstractClientPacket extends BaseClientPacket {

	protected final ClientChannelHandler clientChannelHandler;

	public AbstractClientPacket(ByteBuf channelBuffer, ClientChannelHandler clientChannelHandler, byte opCode) {
		super(channelBuffer, opCode);
		this.clientChannelHandler = clientChannelHandler;
	}
}
