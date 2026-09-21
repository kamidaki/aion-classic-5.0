package com.lostacademy.lostsocket.core;

import java.net.ServerSocket;
import java.net.Socket;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * High-performance, 0% CPU WebSocket server for real-time telemetry streaming to BrService.dll.
 * Executes on virtual threads (Java 21+) and accepts client connections on port 2130.
 */
public class WebSocketServer {

	private static final Logger log = LoggerFactory.getLogger(WebSocketServer.class);
	private static final WebSocketServer instance = new WebSocketServer();

	private ServerSocket serverSocket;
	private final AtomicBoolean isRunning = new AtomicBoolean(false);
	private final Set<WebSocketClientSession> activeSessions = ConcurrentHashMap.newKeySet();

	public static WebSocketServer getInstance() {
		return instance;
	}

	private WebSocketServer() {
	}

	public void start() {
		if (!CustomConfig.TELEMETRY_WEBSOCKET_ENABLE) {
			log.info("[BrSocket] Telemetria WebSocket desativada na configuracao.");
			return;
		}

		if (!isRunning.compareAndSet(false, true)) {
			return;
		}

		int port = CustomConfig.TELEMETRY_WEBSOCKET_PORT;
		String token = CustomConfig.TELEMETRY_WEBSOCKET_TOKEN;

		ThreadPoolManager.getInstance().execute(() -> {
			try {
				serverSocket = new ServerSocket(port);
				log.info("=========================================================================");
				log.info("  BrSocket Telemetry Server escutando na porta: " + port);
				log.info("  Seguranca: Token obrigatorio ativo (X-Token)");
				log.info("=========================================================================");

				while (isRunning.get()) {
					Socket client = serverSocket.accept();
					// Spawn dedicated lightweight Virtual Thread for zero CPU footprint
					Thread.ofVirtual().name("BrSocket-Client-", client.getPort())
						.start(new WebSocketClientSession(client, token, this));
				}
			} catch (Exception e) {
				if (isRunning.get()) {
					log.error("[BrSocket] Erro no listener loop", e);
				}
			}
		});
	}

	public void stop() {
		if (!isRunning.compareAndSet(true, false)) {
			return;
		}

		log.info("[BrSocket] Encerrando servidor de telemetria WebSocket...");
		try {
			if (serverSocket != null && !serverSocket.isClosed()) {
				serverSocket.close();
			}
			for (WebSocketClientSession session : activeSessions) {
				session.close();
			}
			activeSessions.clear();
		} catch (Exception e) {
			log.error("[BrSocket] Erro durante o shutdown do servidor WebSocket", e);
		}
	}

	public void registerSession(WebSocketClientSession session) {
		if (session != null) {
			activeSessions.add(session);
		}
	}

	public void unregisterSession(WebSocketClientSession session) {
		if (session != null) {
			activeSessions.remove(session);
		}
	}

	public void broadcast(String json) {
		if (json == null || activeSessions.isEmpty()) {
			return;
		}
		for (WebSocketClientSession session : activeSessions) {
			session.sendText(json);
		}
	}

	public boolean hasActiveSubscribers() {
		return !activeSessions.isEmpty();
	}

	public int getActiveSessionCount() {
		return activeSessions.size();
	}
}
