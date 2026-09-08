package com.aionemu.commons.configs;

import com.aionemu.commons.configuration.Property;

/**
 * @author Lost Academy Team & Durak
 */
public class DatabaseConfig {

	@Property(key = "database.url")
	public static String DATABASE_URL;

	@Property(key = "database.user")
	public static String DATABASE_USER;

	@Property(key = "database.password")
	public static String DATABASE_PASSWORD;

	/**
	 * Maximum amount of connections kept in connection pool
	 */
	@Property(key = "database.connectionpool.connections.max", defaultValue = "5")
	public static int DATABASE_CONNECTIONS_MAX;

	/**
	 * Minimum amount of connections kept in connection pool
	 */
	@Property(key = "database.connectionpool.connections.min", defaultValue = "2")
	public static int DATABASE_CONNECTIONS_MIN;

	/**
	 * Maximum wait time when getting a DB connection, before throwing a timeout error
	 */
	@Property(key = "database.connectionpool.timeout", defaultValue = "5000")
	public static int DATABASE_TIMEOUT;

	/**
	 * Maximum lifetime of a connection in milliseconds before it is retired (must be shorter than MySQL wait_timeout)
	 */
	@Property(key = "database.connectionpool.maxlifetime", defaultValue = "60000")
	public static long DATABASE_MAX_LIFETIME;

	/**
	 * Maximum idle time for connection in milliseconds
	 */
	@Property(key = "database.connectionpool.idletimeout", defaultValue = "30000")
	public static long DATABASE_IDLE_TIMEOUT;

	/**
	 * Keepalive ping time for idle connections in milliseconds
	 */
	@Property(key = "database.connectionpool.keepalive", defaultValue = "20000")
	public static long DATABASE_KEEPALIVE;

}
