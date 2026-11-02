package com.aionemu.chatserver.network.netty.coder;

import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.handler.codec.MessageToByteEncoder;

/**
 * @author Lost Academy Team & Durak
 */
public class LoginPacketEncoder extends MessageToByteEncoder<ByteBuf> {

	@Override
	protected void encode(ChannelHandlerContext ctx, ByteBuf msg, ByteBuf out) throws Exception {
		int size = msg.readableBytes();
		msg.setShortLE(0, (short) size);
		out.writeBytes(msg);
	}
}
