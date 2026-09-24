package com.aionemu.chatserver.network.netty.security;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import com.aionemu.chatserver.configs.network.NetworkConfig;

/**
 * Tracks per-IP connection rates, active connections, packet rates, and auth attempts.
 */
public final class ClientSecurityManager {

	private static final ClientSecurityManager INSTANCE = new ClientSecurityManager();
	private static final long CLEANUP_INTERVAL_MILLIS = 30_000L;
	private static final long MINUTE_MILLIS = 60_000L;

	private final Map<String, IpRecord> records = new ConcurrentHashMap<>();
	private final AtomicInteger activeConnections = new AtomicInteger();
	private final AtomicLong nextCleanupMillis = new AtomicLong();

	public static ClientSecurityManager getInstance() {
		return INSTANCE;
	}

	private ClientSecurityManager() {
	}

	public Decision acquire(String ip) {
		long now = System.currentTimeMillis();
		cleanupIfDue(now);
		synchronized (records) {
			IpRecord record = records.get(ip);
			if (record == null) {
				if (records.size() >= NetworkConfig.CLIENT_MAX_TRACKED_IPS)
					return Decision.denied("ip_tracker_capacity", 0);
				record = new IpRecord(now);
				records.put(ip, record);
			}
			synchronized (record) {
				if (record.blockedUntilMillis > now)
					return Decision.denied("temporary_blacklist", record.blockedUntilMillis);
				if (now - record.connectionWindowStartMillis >= NetworkConfig.CLIENT_CONNECTION_WINDOW_MILLIS) {
					record.connectionWindowStartMillis = now;
					record.connectionAttempts = 0;
				}
				if (++record.connectionAttempts > NetworkConfig.CLIENT_MAX_CONNECTIONS_PER_WINDOW)
					return blacklist(record, now, "connection_rate_limit");
				if (record.activeConnections >= NetworkConfig.CLIENT_MAX_SIMULTANEOUS_PER_IP)
					return Decision.denied("per_ip_connection_limit", 0);

				int total = activeConnections.incrementAndGet();
				if (total > NetworkConfig.CLIENT_MAX_SIMULTANEOUS) {
					activeConnections.decrementAndGet();
					return Decision.denied("global_connection_limit", 0);
				}
				record.activeConnections++;
				record.lastSeenMillis = now;
				return Decision.accepted();
			}
		}
	}

	public void release(String ip) {
		if (ip == null)
			return;
		IpRecord record = records.get(ip);
		if (record == null)
			return;
		synchronized (record) {
			if (record.activeConnections > 0) {
				record.activeConnections--;
				activeConnections.decrementAndGet();
			}
			record.lastSeenMillis = System.currentTimeMillis();
		}
	}

	public Decision checkPacketRate(String ip) {
		long now = System.currentTimeMillis();
		IpRecord record = records.get(ip);
		if (record == null)
			return Decision.denied("unregistered_connection", 0);
		synchronized (record) {
			if (record.blockedUntilMillis > now)
				return Decision.denied("temporary_blacklist", record.blockedUntilMillis);
			if (now - record.packetWindowStartMillis >= 1_000L) {
				record.packetWindowStartMillis = now;
				record.packetCount = 0;
			}
			if (++record.packetCount > NetworkConfig.CLIENT_MAX_PACKETS_PER_SECOND)
				return blacklist(record, now, "packet_rate_limit");
			record.lastSeenMillis = now;
			return Decision.accepted();
		}
	}

	public Decision checkAuthenticationAttempt(String ip) {
		long now = System.currentTimeMillis();
		IpRecord record = records.get(ip);
		if (record == null)
			return Decision.denied("unregistered_connection", 0);
		synchronized (record) {
			if (record.blockedUntilMillis > now)
				return Decision.denied("temporary_blacklist", record.blockedUntilMillis);
			if (now - record.authenticationWindowStartMillis >= MINUTE_MILLIS) {
				record.authenticationWindowStartMillis = now;
				record.authenticationAttempts = 0;
			}
			if (++record.authenticationAttempts > NetworkConfig.CLIENT_MAX_AUTH_ATTEMPTS_PER_MINUTE)
				return blacklist(record, now, "authentication_rate_limit");
			return Decision.accepted();
		}
	}

	public Decision recordInvalidEvent(String ip, String reason) {
		long now = System.currentTimeMillis();
		IpRecord record = records.get(ip);
		if (record == null)
			return Decision.denied(reason, 0);
		synchronized (record) {
			if (now - record.invalidWindowStartMillis >= MINUTE_MILLIS) {
				record.invalidWindowStartMillis = now;
				record.invalidEvents = 0;
			}
			if (++record.invalidEvents >= NetworkConfig.CLIENT_MAX_INVALID_PACKETS_PER_MINUTE)
				return blacklist(record, now, reason);
			return Decision.denied(reason, record.blockedUntilMillis);
		}
	}

	private Decision blacklist(IpRecord record, long now, String reason) {
		if (NetworkConfig.CLIENT_TEMPORARY_BLACKLIST_SECONDS > 0)
			record.blockedUntilMillis = Math.max(record.blockedUntilMillis,
				now + NetworkConfig.CLIENT_TEMPORARY_BLACKLIST_SECONDS * 1_000L);
		return Decision.denied(reason, record.blockedUntilMillis);
	}

	private void cleanupIfDue(long now) {
		long next = nextCleanupMillis.get();
		if (now < next || !nextCleanupMillis.compareAndSet(next, now + CLEANUP_INTERVAL_MILLIS))
			return;
		synchronized (records) {
			records.entrySet().removeIf(entry -> entry.getValue().isExpired(now));
		}
	}

	public record Decision(boolean allowed, String reason, long blockedUntilMillis) {
		private static Decision accepted() {
			return new Decision(true, "accepted", 0);
		}

		private static Decision denied(String reason, long blockedUntilMillis) {
			return new Decision(false, reason, blockedUntilMillis);
		}
	}

	private static final class IpRecord {
		private long connectionWindowStartMillis;
		private long packetWindowStartMillis;
		private long authenticationWindowStartMillis;
		private long invalidWindowStartMillis;
		private long blockedUntilMillis;
		private long lastSeenMillis;
		private int connectionAttempts;
		private int packetCount;
		private int authenticationAttempts;
		private int invalidEvents;
		private int activeConnections;

		private IpRecord(long now) {
			connectionWindowStartMillis = packetWindowStartMillis = authenticationWindowStartMillis = invalidWindowStartMillis = lastSeenMillis = now;
		}

		private synchronized boolean isExpired(long now) {
			return activeConnections == 0 && blockedUntilMillis <= now && now - lastSeenMillis > 2 * MINUTE_MILLIS;
		}
	}
}
