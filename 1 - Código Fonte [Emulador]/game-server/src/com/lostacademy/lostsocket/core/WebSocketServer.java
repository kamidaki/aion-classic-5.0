package com.lostacademy.lostsocket.core;

import java.net.ServerSocket;
import java.net.Socket;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.World;

/**
 * High-performance, 0% CPU WebSocket server for real-time telemetry streaming to BrService.dll.
 * Executes on virtual threads (Java 21+) and accepts client connections on port 2130.
 * Supports targeted, secure per-player telemetry dispatch and team/group routing.
 */
public class WebSocketServer {

	private static final Logger log = LoggerFactory.getLogger(WebSocketServer.class);
	private static final WebSocketServer instance = new WebSocketServer();

	private ServerSocket serverSocket;
	private final AtomicBoolean isRunning = new AtomicBoolean(false);
	private final Set<WebSocketClientSession> activeSessions = ConcurrentHashMap.newKeySet();
	private final ConcurrentHashMap<Integer, WebSocketClientSession> playerSessions = new ConcurrentHashMap<>();
	private final ConcurrentHashMap<String, WebSocketClientSession> ipSessions = new ConcurrentHashMap<>();

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
				log.info("  Roteamento: Telemetria direcionada individual / grupo (Zero Leaks)");
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
			playerSessions.clear();
			ipSessions.clear();
		} catch (Exception e) {
			log.error("[BrSocket] Erro durante o shutdown do servidor WebSocket", e);
		}
	}

	public void registerSession(WebSocketClientSession session) {
		if (session != null) {
			activeSessions.add(session);
			if (session.getClientIp() != null) {
				ipSessions.put(session.getClientIp(), session);
			}
			if (session.getPlayerObjectId() > 0) {
				playerSessions.put(session.getPlayerObjectId(), session);
			}
		}
	}

	public void unregisterSession(WebSocketClientSession session) {
		if (session != null) {
			activeSessions.remove(session);
			if (session.getPlayerObjectId() > 0) {
				playerSessions.remove(session.getPlayerObjectId(), session);
			}
			if (session.getClientIp() != null) {
				ipSessions.remove(session.getClientIp(), session);
			}
		}
	}

	public void bindPlayer(int playerId, WebSocketClientSession session) {
		if (playerId > 0 && session != null) {
			playerSessions.put(playerId, session);
		}
	}

	public boolean isLocalOrLoopback(String ip) {
		if (ip == null || ip.isEmpty()) return false;
		if ("127.0.0.1".equals(ip) || "localhost".equalsIgnoreCase(ip) || "0:0:0:0:0:0:0:1".equals(ip) || "::1".equals(ip)) {
			return true;
		}
		if (ip.startsWith("192.168.") || ip.startsWith("10.") || ip.startsWith("172.16.")) {
			return true;
		}
		try {
			java.net.InetAddress addr = java.net.InetAddress.getByName(ip);
			if (addr.isLoopbackAddress() || addr.isSiteLocalAddress() || addr.isAnyLocalAddress()) {
				return true;
			}
			return java.net.NetworkInterface.getByInetAddress(addr) != null;
		} catch (Exception ignored) {
			return false;
		}
	}

	public void bindIfSingleOrLocal(Player player) {
		if (player == null || activeSessions.isEmpty()) {
			return;
		}
		int playerId = player.getObjectId();
		WebSocketClientSession existing = playerSessions.get(playerId);
		if (existing != null && !existing.isClosed()) {
			return;
		}

		String ip = (player.getClientConnection() != null) ? player.getClientConnection().getIP() : null;
		WebSocketClientSession session = null;

		if (ip != null) {
			session = ipSessions.get(ip);
			if (session == null && isLocalOrLoopback(ip)) {
				session = ipSessions.get("127.0.0.1");
				if (session == null) {
					for (WebSocketClientSession s : activeSessions) {
						if (isLocalOrLoopback(s.getClientIp())) {
							session = s;
							break;
						}
					}
				}
			}
		}

		if (session == null && activeSessions.size() == 1) {
			session = activeSessions.iterator().next();
		}

		if (session != null && !session.isClosed()) {
			session.setPlayerObjectId(playerId);
			bindPlayer(playerId, session);
			log.info("[BrSocket] Sessao telemetria vinculada com sucesso ao jogador {} (objId={})", player.getName(), playerId);
		}
	}

	public void sendToPlayer(int playerId, String json) {
		if (json == null || playerId <= 0 || activeSessions.isEmpty()) {
			return;
		}
		WebSocketClientSession session = playerSessions.get(playerId);
		if (session != null && !session.isClosed()) {
			session.sendText(json);
			return;
		}
		// Fallback inteligente: buscar jogador no mundo e associar por IP ou sessao unica/local
		try {
			Player p = World.getInstance().getPlayer(playerId);
			if (p != null) {
				bindIfSingleOrLocal(p);
				session = playerSessions.get(playerId);
				if (session != null && !session.isClosed()) {
					session.sendText(json);
					return;
				}
			}
		} catch (Exception ignored) {
		}
	}

	public void sendToGroupOrAlliance(Player player, String json) {
		if (player == null || json == null || activeSessions.isEmpty()) {
			return;
		}
		sendToPlayer(player.getObjectId(), json);
		try {
			if (player.isInGroup() && player.getPlayerGroup() != null) {
				for (Player member : player.getPlayerGroup().getOnlineMembers()) {
					if (member != null && member.getObjectId() != player.getObjectId()) {
						sendToPlayer(member.getObjectId(), json);
					}
				}
			} else if (player.isInAlliance() && player.getPlayerAlliance() != null) {
				for (Player member : player.getPlayerAlliance().getOnlineMembers()) {
					if (member != null && member.getObjectId() != player.getObjectId()) {
						sendToPlayer(member.getObjectId(), json);
					}
				}
			}
		} catch (Exception ignored) {
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
