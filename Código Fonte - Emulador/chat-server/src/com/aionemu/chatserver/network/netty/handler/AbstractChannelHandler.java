package com.aionemu.chatserver.network.netty.handler;

import java.io.IOException;
import java.net.InetAddress;

import io.netty.channel.Channel;
import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.chatserver.common.netty.BaseServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class AbstractChannelHandler extends ChannelInboundHandlerAdapter {

	private static final Logger log = LoggerFactory.getLogger(AbstractChannelHandler.class);

	protected InetAddress inetAddress;
	protected Channel associatedChannel;

	@Override
	public void channelInactive(ChannelHandlerContext ctx) throws Exception {
		log.info("Channel disconnected IP: {}", inetAddress != null ? inetAddress.getHostAddress() : "UNKNOWN");
		super.channelInactive(ctx);
	}

	@Override
	public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) throws Exception {
		if (cause instanceof IOException)
			return;
		log.error("Caught exception from netty", cause);
	}

	public void close(BaseServerPacket packet) {
		if (associatedChannel != null) {
			associatedChannel.writeAndFlush(packet).addListener(ChannelFutureListener.CLOSE);
		}
	}

	public void close() {
		if (associatedChannel != null) {
			associatedChannel.close();
		}
	}

	public String getIP() {
		return inetAddress != null ? inetAddress.getHostAddress() : "UNKNOWN";
	}
}
