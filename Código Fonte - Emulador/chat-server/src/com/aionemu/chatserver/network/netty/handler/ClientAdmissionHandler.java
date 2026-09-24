package com.aionemu.chatserver.network.netty.handler;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.concurrent.atomic.AtomicBoolean;

import org.jboss.netty.channel.ChannelHandlerContext;
import org.jboss.netty.channel.ChannelStateEvent;
import org.jboss.netty.channel.MessageEvent;
import org.jboss.netty.channel.SimpleChannelUpstreamHandler;
import org.jboss.netty.channel.group.ChannelGroup;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.chatserver.network.netty.security.ClientSecurityManager;
import com.aionemu.chatserver.network.netty.security.ClientSecurityManager.Decision;
import com.aionemu.chatserver.network.netty.security.SecurityEventLogger;
import com.aionemu.commons.network.GeoIPFilterService;

/**
 * Performs GeoIP, connection, and packet-rate checks before events enter the worker executor.
 */
public final class ClientAdmissionHandler extends SimpleChannelUpstreamHandler {

	private static final Logger log = LoggerFactory.getLogger(ClientAdmissionHandler.class);
	private final ChannelGroup channelGroup;
	private final AtomicBoolean acquired = new AtomicBoolean();
	private String ip;

	public ClientAdmissionHandler(ChannelGroup channelGroup) {
		this.channelGroup = channelGroup;
	}

	@Override
	public void channelOpen(ChannelHandlerContext ctx, ChannelStateEvent e) throws Exception {
		channelGroup.add(e.getChannel());
		super.channelOpen(ctx, e);
	}

	@Override
	public void channelConnected(ChannelHandlerContext ctx, ChannelStateEvent e) throws Exception {
		InetAddress address = remoteAddress(e.getChannel().getRemoteAddress());
		ip = address == null ? null : address.getHostAddress();
		if (address == null || !GeoIPFilterService.isAllowed(address)) {
			SecurityEventLogger.warn(log, "geoip_rejection", e.getChannel().getId(), ip, "remote address is outside the allow-list");
			e.getChannel().close();
			return;
		}

		Decision decision = ClientSecurityManager.getInstance().acquire(ip);
		if (!decision.allowed()) {
			SecurityEventLogger.warn(log, "connection_rejection", e.getChannel().getId(), ip, decision.reason());
			e.getChannel().close();
			return;
		}
		acquired.set(true);
		super.channelConnected(ctx, e);
	}

	@Override
	public void messageReceived(ChannelHandlerContext ctx, MessageEvent e) throws Exception {
		if (!acquired.get()) {
			e.getChannel().close();
			return;
		}
		Decision decision = ClientSecurityManager.getInstance().checkPacketRate(ip);
		if (!decision.allowed()) {
			SecurityEventLogger.warn(log, "flood_detection", e.getChannel().getId(), ip, decision.reason());
			e.getChannel().close();
			return;
		}
		super.messageReceived(ctx, e);
	}

	@Override
	public void channelDisconnected(ChannelHandlerContext ctx, ChannelStateEvent e) throws Exception {
		release();
		super.channelDisconnected(ctx, e);
	}

	@Override
	public void channelClosed(ChannelHandlerContext ctx, ChannelStateEvent e) throws Exception {
		release();
		super.channelClosed(ctx, e);
	}

	private void release() {
		if (acquired.compareAndSet(true, false))
			ClientSecurityManager.getInstance().release(ip);
	}

	private static InetAddress remoteAddress(SocketAddress remote) {
		return remote instanceof InetSocketAddress socketAddress ? socketAddress.getAddress() : null;
	}
}
