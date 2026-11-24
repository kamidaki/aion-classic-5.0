package com.aionemu.chatserver.network.netty.handler;

import java.net.InetSocketAddress;
import java.nio.ByteOrder;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelHandlerContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.chatserver.model.ChatClient;
import com.aionemu.chatserver.network.aion.AbstractClientPacket;
import com.aionemu.chatserver.network.aion.AbstractServerPacket;
import com.aionemu.chatserver.network.aion.ClientPacketHandler;

/**
 * @author Lost Academy Team & Durak
 */
public class ClientChannelHandler extends AbstractChannelHandler {

	private static final Logger log = LoggerFactory.getLogger(ClientChannelHandler.class);
	private final ClientPacketHandler clientPacketHandler;
	private ClientChannelHandlerState state;
	private ChatClient chatClient;

	public ClientChannelHandler(ClientPacketHandler clientPacketHandler) {
		this.clientPacketHandler = clientPacketHandler;
	}

	@Override
	public void channelActive(ChannelHandlerContext ctx) throws Exception {
		super.channelActive(ctx);
		state = ClientChannelHandlerState.CONNECTED;
		inetAddress = ((InetSocketAddress) ctx.channel().remoteAddress()).getAddress();
		associatedChannel = ctx.channel();
		log.info("Channel connected Ip: {}", inetAddress.getHostAddress());
	}

	@Override
	public void channelRead(ChannelHandlerContext ctx, Object msg) throws Exception {
		ByteBuf buf = ((ByteBuf) msg).order(ByteOrder.LITTLE_ENDIAN);
		try {
			AbstractClientPacket clientPacket = clientPacketHandler.handle(buf, this);
			if (clientPacket != null && clientPacket.read())
				clientPacket.run();
			if (clientPacket != null)
				log.debug("Received packet: {}", clientPacket);
		} finally {
			buf.release();
		}
	}

	public void sendPacket(AbstractServerPacket packet) {
		ByteBuf cb = Unpooled.buffer(2 * 8192).order(ByteOrder.LITTLE_ENDIAN);
		packet.write(this, cb);
		associatedChannel.writeAndFlush(cb);
		log.debug("Sent packet: {}", packet);
	}

	public ClientChannelHandlerState getState() {
		return state;
	}

	public void setState(ClientChannelHandlerState state) {
		this.state = state;
	}

	public ChatClient getChatClient() {
		return chatClient;
	}

	public void setChatClient(ChatClient chatClient) {
		this.chatClient = chatClient;
	}

	public enum ClientChannelHandlerState {
		CONNECTED,
		AUTHED
	}
}
