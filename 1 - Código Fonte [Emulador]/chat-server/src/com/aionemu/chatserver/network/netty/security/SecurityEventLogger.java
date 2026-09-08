package com.aionemu.chatserver.network.netty.security;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;

import com.aionemu.chatserver.configs.network.NetworkConfig;

/** Aggregates repeated security events by category and remote IP to prevent log amplification. */
public final class SecurityEventLogger {

	private static final Map<String, EventWindow> WINDOWS = new ConcurrentHashMap<>();
	private static final AtomicLong NEXT_CLEANUP_MILLIS = new AtomicLong();
	private static final EventWindow OVERFLOW_WINDOW = new EventWindow();

	private SecurityEventLogger() {
	}

	public static void warn(Logger log, String category, int connectionId, String ip, String detail) {
		long now = System.currentTimeMillis();
		cleanupIfDue(now);
		String safeIp = ip == null ? "unavailable" : ip;
		String key = category + '|' + safeIp;
		EventWindow window = WINDOWS.get(key);
		if (window == null) {
			synchronized (WINDOWS) {
				window = WINDOWS.get(key);
				if (window == null) {
					if (WINDOWS.size() >= NetworkConfig.CLIENT_MAX_TRACKED_IPS)
						window = OVERFLOW_WINDOW;
					else {
						window = new EventWindow();
						WINDOWS.put(key, window);
					}
				}
			}
		}
		int suppressed = window.tryLog(now);
		if (suppressed < 0)
			return;
		
		log.warn("security_event={} connection_id={} remote_ip={} detail={} suppressed_repeats={}", category, connectionId, safeIp, detail,
			suppressed);
	}

	private static void cleanupIfDue(long now) {
		long next = NEXT_CLEANUP_MILLIS.get();
		long interval = Math.max(1, NetworkConfig.CLIENT_LOG_AGGREGATION_WINDOW_SECONDS) * 1_000L;
		if (now < next || !NEXT_CLEANUP_MILLIS.compareAndSet(next, now + interval))
			return;
		WINDOWS.entrySet().removeIf(entry -> now - entry.getValue().lastEventMillis() > interval * 2);
	}

	private static final class EventWindow {
		private long lastLogMillis;
		private long lastEventMillis;
		private int suppressed;

		private synchronized int tryLog(long now) {
			lastEventMillis = now;
			long interval = Math.max(1, NetworkConfig.CLIENT_LOG_AGGREGATION_WINDOW_SECONDS) * 1_000L;
			if (lastLogMillis != 0 && now - lastLogMillis < interval) {
				suppressed++;
				return -1;
			}
			int result = suppressed;
			suppressed = 0;
			lastLogMillis = now;
			return result;
		}

		private synchronized long lastEventMillis() {
			return lastEventMillis;
		}
	}
}
