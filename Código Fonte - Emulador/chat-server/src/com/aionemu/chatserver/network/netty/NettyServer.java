package com.aionemu.chatserver.network.netty;

import java.util.concurrent.Executors;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.group.ChannelGroup;
import io.netty.channel.group.DefaultChannelGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.util.concurrent.GlobalEventExecutor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.chatserver.configs.network.NetworkConfig;
import com.aionemu.chatserver.network.aion.ClientPacketHandler;
import com.aionemu.chatserver.network.gameserver.GsConnectionFactoryImpl;
import com.aionemu.chatserver.network.netty.pipeline.LoginToClientPipeLineFactory;
import com.aionemu.commons.network.NioServer;
import com.aionemu.commons.network.ServerCfg;

/**
 * @author Lost Academy Team & Durak
 */
public class NettyServer {

	private static final Logger log = LoggerFactory.getLogger(NettyServer.class);
	private static final NettyServer instance = new NettyServer();
	private final EventLoopGroup bossGroup;
	private final EventLoopGroup workerGroup;
	private final ChannelGroup aionClientChannelGroup;
	private final LoginToClientPipeLineFactory pipelineFactory;
	private final NioServer nioServer;

	public static NettyServer getInstance() {
		return instance;
	}

	private NettyServer() {
		bossGroup = new NioEventLoopGroup(1);
		workerGroup = new NioEventLoopGroup(NetworkConfig.NIO_READ_WRITE_THREADS + 1);
		aionClientChannelGroup = new DefaultChannelGroup(GlobalEventExecutor.INSTANCE);
		pipelineFactory = new LoginToClientPipeLineFactory(new ClientPacketHandler(), aionClientChannelGroup);

		initChannel(new ServerCfg(NetworkConfig.CLIENT_SOCKET_ADDRESS, "Aion game clients", null));

		nioServer = new NioServer(NetworkConfig.NIO_READ_WRITE_THREADS,
			new ServerCfg(NetworkConfig.GAMESERVER_SOCKET_ADDRESS, "game servers", new GsConnectionFactoryImpl()));
		nioServer.connect(Executors.newSingleThreadExecutor());
	}

	private void initChannel(ServerCfg gameClientConfig) {
		ServerBootstrap bootstrap = new ServerBootstrap();
		bootstrap.group(bossGroup, workerGroup)
			.channel(NioServerSocketChannel.class)
			.childHandler(pipelineFactory)
			.childOption(ChannelOption.TCP_NODELAY, true)
			.childOption(ChannelOption.SO_KEEPALIVE, true)
			.childOption(ChannelOption.SO_REUSEADDR, true)
			.childOption(ChannelOption.CONNECT_TIMEOUT_MILLIS, 100);

		try {
			Channel channel = bootstrap.bind(gameClientConfig.address()).sync().channel();
			aionClientChannelGroup.add(channel);
			log.info("Listening on " + gameClientConfig.getAddressInfo() + " for " + gameClientConfig.clientDescription());
		} catch (InterruptedException e) {
			Thread.currentThread().interrupt();
			log.error("Failed to bind Netty channel", e);
		}
	}

	public void shutdownAll() {
		aionClientChannelGroup.close().awaitUninterruptibly();
		bossGroup.shutdownGracefully();
		workerGroup.shutdownGracefully();
		pipelineFactory.shutdown();
		nioServer.shutdown();
	}
}
