package com.aionemu.chatserver.network.netty.handler;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.concurrent.atomic.AtomicBoolean;

import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.group.ChannelGroup;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.chatserver.network.netty.security.ClientSecurityManager;
import com.aionemu.chatserver.network.netty.security.ClientSecurityManager.Decision;
import com.aionemu.chatserver.network.netty.security.SecurityEventLogger;
import com.aionemu.commons.network.GeoIPFilterService;

/**
 * Performs GeoIP, connection, and packet-rate checks before events enter the worker executor.
 */
public final class ClientAdmissionHandler extends ChannelInboundHandlerAdapter {

	private static final Logger log = LoggerFactory.getLogger(ClientAdmissionHandler.class);
	private final ChannelGroup channelGroup;
	private final AtomicBoolean acquired = new AtomicBoolean();
	private String ip;

	public ClientAdmissionHandler(ChannelGroup channelGroup) {
		this.channelGroup = channelGroup;
	}

	@Override
	public void channelActive(ChannelHandlerContext ctx) throws Exception {
		channelGroup.add(ctx.channel());
		InetAddress address = remoteAddress(ctx.channel().remoteAddress());
		ip = address == null ? null : address.getHostAddress();
		if (address == null || !GeoIPFilterService.isAllowed(address)) {
			SecurityEventLogger.warn(log, "geoip_rejection", ctx.channel().id().hashCode(), ip, "remote address is outside the allow-list");
			ctx.channel().close();
			return;
		}

		Decision decision = ClientSecurityManager.getInstance().acquire(ip);
		if (!decision.allowed()) {
			SecurityEventLogger.warn(log, "connection_rejection", ctx.channel().id().hashCode(), ip, decision.reason());
			ctx.channel().close();
			return;
		}
		acquired.set(true);
		super.channelActive(ctx);
	}

	@Override
	public void channelRead(ChannelHandlerContext ctx, Object msg) throws Exception {
		if (!acquired.get()) {
			ctx.channel().close();
			return;
		}
		Decision decision = ClientSecurityManager.getInstance().checkPacketRate(ip);
		if (!decision.allowed()) {
			SecurityEventLogger.warn(log, "flood_detection", ctx.channel().id().hashCode(), ip, decision.reason());
			ctx.channel().close();
			return;
		}
		ctx.fireChannelRead(msg);
	}

	@Override
	public void channelInactive(ChannelHandlerContext ctx) throws Exception {
		release();
		super.channelInactive(ctx);
	}

	private void release() {
		if (acquired.compareAndSet(true, false))
			ClientSecurityManager.getInstance().release(ip);
	}

	private static InetAddress remoteAddress(SocketAddress remote) {
		return remote instanceof InetSocketAddress socketAddress ? socketAddress.getAddress() : null;
	}
}
