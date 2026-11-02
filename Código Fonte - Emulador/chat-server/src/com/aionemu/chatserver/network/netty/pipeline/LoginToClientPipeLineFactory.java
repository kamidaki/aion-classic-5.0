package com.aionemu.chatserver.network.netty.pipeline;

import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelPipeline;
import io.netty.channel.group.ChannelGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.util.concurrent.DefaultEventExecutorGroup;
import io.netty.util.concurrent.EventExecutorGroup;

import com.aionemu.chatserver.network.aion.ClientPacketHandler;
import com.aionemu.chatserver.network.netty.coder.LoginPacketDecoder;
import com.aionemu.chatserver.network.netty.coder.LoginPacketEncoder;
import com.aionemu.chatserver.network.netty.coder.PacketFrameDecoder;
import com.aionemu.chatserver.network.netty.handler.ClientAdmissionHandler;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;

/**
 * @author Lost Academy Team & Durak
 */
public class LoginToClientPipeLineFactory extends ChannelInitializer<SocketChannel> {

	private static final int THREADS_MAX = 10;
	private final ClientPacketHandler clientPacketHandler;
	private final ChannelGroup channelGroup;
	private final EventExecutorGroup executorGroup;

	public LoginToClientPipeLineFactory(ClientPacketHandler clientPacketHandler, ChannelGroup channelGroup) {
		this.clientPacketHandler = clientPacketHandler;
		this.channelGroup = channelGroup;
		this.executorGroup = new DefaultEventExecutorGroup(THREADS_MAX);
	}

	public LoginToClientPipeLineFactory(ClientPacketHandler clientPacketHandler) {
		this(clientPacketHandler, null);
	}

	@Override
	protected void initChannel(SocketChannel ch) throws Exception {
		ChannelPipeline pipeline = ch.pipeline();
		pipeline.addLast("framedecoder", new PacketFrameDecoder());
		pipeline.addLast("packetdecoder", new LoginPacketDecoder());
		if (channelGroup != null) {
			pipeline.addLast("admission", new ClientAdmissionHandler(channelGroup));
		}
		pipeline.addLast("packetencoder", new LoginPacketEncoder());
		pipeline.addLast(executorGroup, "handler", new ClientChannelHandler(clientPacketHandler));
	}

	public void shutdown() {
		executorGroup.shutdownGracefully();
	}
}
