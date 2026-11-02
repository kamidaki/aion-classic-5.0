package com.aionemu.chatserver.network.aion.clientpackets;

import java.nio.charset.StandardCharsets;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.network.aion.AbstractClientPacket;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;
import com.aionemu.chatserver.service.ChatService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_CHANNEL_REQUEST extends AbstractClientPacket {

	private int channelRequestId;
	private byte[] channelIdentifier;

	public CM_CHANNEL_REQUEST(ByteBuf channelBuffer, ClientChannelHandler clientChannelHandler, byte opCode) {
		super(channelBuffer, clientChannelHandler, opCode);
	}

	@Override
	protected void readImpl() {
		readC(); // 0x40 = @
		readH(); // 0
		channelRequestId = readD(); // client increases this by 1 for each request (e.g. after teleport)
		readB(16); // 0
		int length = (readH() * 2);
		channelIdentifier = readB(length);
		readD(); // 0
	}

	@Override
	protected void runImpl() {
		ChatService.getInstance().registerPlayerWithChannel(clientChannelHandler, channelRequestId,
			new String(channelIdentifier, StandardCharsets.UTF_16LE));
	}
}
