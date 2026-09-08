package com.aionemu.chatserver.configs.network;

import java.net.InetSocketAddress;

import com.aionemu.commons.configuration.Property;

public class NetworkConfig {

	/**
	 * Address where Aion clients will attempt to connect to (host/domain name or IP)
	 */
	@Property(key = "chatserver.network.client.connect_address", defaultValue = "0.0.0.0:10241")
	public static InetSocketAddress CLIENT_CONNECT_ADDRESS;

	/**
	 * Local address where CS will listen for Aion client connections (0.0.0.0 = bind any local IP)
	 */
	@Property(key = "chatserver.network.client.socket_address", defaultValue = "0.0.0.0:10241")
	public static InetSocketAddress CLIENT_SOCKET_ADDRESS;

	/**
	 * Local address where CS will listen for GS connections (0.0.0.0 = bind any local IP)
	 */
	@Property(key = "chatserver.network.gameserver.socket_address", defaultValue = "0.0.0.0:9021")
	public static InetSocketAddress GAMESERVER_SOCKET_ADDRESS;

	/**
	 * Password for GS authentication
	 */
	@Property(key = "chatserver.network.gameserver.password", defaultValue = "")
	public static String GAMESERVER_PASSWORD;

	/**
	 * Number of threads dedicated to be doing io read & write. There is always 1 acceptor thread. If value is < 1 - acceptor thread will also handle
	 * read & write. If value is > 0 - there will be given amount of read & write threads + 1 acceptor thread.
	 */
	@Property(key = "chatserver.network.nio.threads", defaultValue = "1")
	public static int NIO_READ_WRITE_THREADS;

	/** Maximum accepted client frame size, including the two-byte length field. */
	@Property(key = "chatserver.network.client.max_frame_length", defaultValue = "16384")
	public static int CLIENT_MAX_FRAME_LENGTH;

	/** Maximum number of decoded packets accepted from one IP per second. */
	@Property(key = "chatserver.network.client.max_packets_per_second", defaultValue = "40")
	public static int CLIENT_MAX_PACKETS_PER_SECOND;

	/** Number of consecutive unsupported opcodes tolerated before disconnect. */
	@Property(key = "chatserver.network.client.unknown_packets_threshold", defaultValue = "2")
	public static int CLIENT_UNKNOWN_PACKET_THRESHOLD;

	/** Number of malformed packet payloads tolerated before disconnect. */
	@Property(key = "chatserver.network.client.malformed_packets_threshold", defaultValue = "1")
	public static int CLIENT_MALFORMED_PACKET_THRESHOLD;

	/** Window used for limiting new connections from one IP. */
	@Property(key = "chatserver.network.client.connection_window_ms", defaultValue = "10000")
	public static int CLIENT_CONNECTION_WINDOW_MILLIS;

	/** Maximum new connections accepted from one IP per connection window. */
	@Property(key = "chatserver.network.client.max_connections_per_window", defaultValue = "15")
	public static int CLIENT_MAX_CONNECTIONS_PER_WINDOW;

	/** Maximum simultaneous client connections from one IP. */
	@Property(key = "chatserver.network.client.max_simultaneous_per_ip", defaultValue = "5")
	public static int CLIENT_MAX_SIMULTANEOUS_PER_IP;

	/** Maximum simultaneous Aion client connections across the Chat Server. */
	@Property(key = "chatserver.network.client.max_simultaneous", defaultValue = "2000")
	public static int CLIENT_MAX_SIMULTANEOUS;

	/** Maximum authentication attempts from one IP per minute. */
	@Property(key = "chatserver.network.client.max_auth_attempts_per_minute", defaultValue = "5")
	public static int CLIENT_MAX_AUTH_ATTEMPTS_PER_MINUTE;

	/** Invalid events from one IP per minute before a temporary blacklist is applied. */
	@Property(key = "chatserver.network.client.max_invalid_packets_per_minute", defaultValue = "3")
	public static int CLIENT_MAX_INVALID_PACKETS_PER_MINUTE;

	/** Duration of the in-memory IP blacklist. Zero disables temporary blacklisting. */
	@Property(key = "chatserver.network.client.temporary_blacklist_seconds", defaultValue = "900")
	public static int CLIENT_TEMPORARY_BLACKLIST_SECONDS;

	/** Disconnect channels which have not produced a complete frame in this time. */
	@Property(key = "chatserver.network.client.read_timeout_seconds", defaultValue = "30")
	public static int CLIENT_READ_TIMEOUT_SECONDS;

	/** Time used to aggregate repeated security log events. */
	@Property(key = "chatserver.network.client.log_aggregation_window_seconds", defaultValue = "60")
	public static int CLIENT_LOG_AGGREGATION_WINDOW_SECONDS;

	/** Maximum IP records retained by the in-memory limiter. */
	@Property(key = "chatserver.network.client.max_tracked_ips", defaultValue = "100000")
	public static int CLIENT_MAX_TRACKED_IPS;
}
