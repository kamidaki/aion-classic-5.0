package com.aionemu.chatserver.network.aion.clientpackets;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.network.aion.AbstractClientPacket;
import com.aionemu.chatserver.network.aion.serverpackets.SM_CHAT_INI;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_CHAT_INI extends AbstractClientPacket {

	public CM_CHAT_INI(ByteBuf channelBuffer, ClientChannelHandler clientChannelHandler, byte opCode) {
		super(channelBuffer, clientChannelHandler, opCode);
	}

	@Override
	protected void readImpl() {
		readC();
		readH();
		readD();
		readD();
		readD();
	}

	@Override
	protected void runImpl() {
		clientChannelHandler.sendPacket(new SM_CHAT_INI());
	}
}
