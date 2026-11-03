package com.aionemu.gameserver.web;

import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.model.ChatType;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.player.PlayerService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.World;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Collection;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Servidor Web Local Integrado para Aion Shop (Black Cloud Marketplace), Aion Today
 * e API de Controle Seguro para o Aion Cloud Port Manager.
 */
public class LocalWebServer {

	private static final Logger log = LoggerFactory.getLogger(LocalWebServer.class);
	private static final LocalWebServer instance = new LocalWebServer();

	private HttpServer server;
	private HttpServer controlServer;
	private final int port = 7778;
	private final int controlPort = 7778;

	private final AtomicBoolean restartCountdownRunning = new AtomicBoolean(false);
	private final AtomicInteger restartRemainingSeconds = new AtomicInteger(0);
	private final AtomicBoolean restartConfirmed = new AtomicBoolean(false);
	private final AtomicInteger lastKickedPlayersCount = new AtomicInteger(0);

	public static LocalWebServer getInstance() {
		return instance;
	}

	public synchronized void start(int portToUse) {
		int targetPort = (portToUse > 0) ? portToUse : controlPort;
		if (targetPort == 8080) {
			// Port 8080 is reserved strictly for Aion Cloud Port Gateway; defer to dedicated port 7778
			targetPort = controlPort;
		}

		if (controlServer == null) {
			try {
				controlServer = HttpServer.create(new InetSocketAddress("127.0.0.1", controlPort), 0);
				controlServer.setExecutor(Executors.newFixedThreadPool(4));
				registerContexts(controlServer);
				controlServer.start();
				log.info("GameServer Cloud Control API e LocalWebServer escutando em http://127.0.0.1:{}", controlPort);
			} catch (IOException e) {
				log.warn("Nao foi possivel iniciar GameServer Cloud Control API na porta {}: {}", controlPort, e.getMessage());
			}
		}
	}

	private void registerContexts(HttpServer srv) {
		srv.createContext("/", new RootHandler());
		srv.createContext("/shop", new ShopHandler());
		srv.createContext("/today", new TodayHandler());
		srv.createContext("/api/status", new StatusApiHandler());
		srv.createContext("/api/cloud/safe-client-restart", new SafeClientRestartHandler());
		srv.createContext("/api/cloud/safe-client-restart-status", new SafeClientRestartStatusHandler());
	}

	public synchronized void stop() {
		if (server != null) {
			server.stop(0);
			server = null;
			log.info("LocalWebServer finalizado.");
		}
		if (controlServer != null) {
			controlServer.stop(0);
			controlServer = null;
			log.info("GameServer Cloud Control API finalizada.");
		}
	}

	private void startClientRestartCountdown(int initialSeconds) {
		if (!restartCountdownRunning.compareAndSet(false, true)) {
			return;
		}
		restartConfirmed.set(false);
		restartRemainingSeconds.set(initialSeconds);

		broadcastClientRestartNotice(initialSeconds);
		scheduleNextCountdownTick();
	}

	private void scheduleNextCountdownTick() {
		ThreadPoolManager.getInstance().schedule(() -> {
			try {
				Collection<Player> players = World.getInstance().getAllPlayers();
				if (players.isEmpty()) {
					restartRemainingSeconds.set(0);
					restartConfirmed.set(true);
					restartCountdownRunning.set(false);
					log.info("[CloudControl] Todos os jogadores desconectaram antes do fim da contagem. Reinicio seguro liberado.");
					return;
				}

				int remaining = restartRemainingSeconds.decrementAndGet();
				if (remaining <= 0) {
					int kicked = 0;
					for (Player player : players) {
						try {
							PlayerService.storePlayer(player);
							if (player.getClientConnection() != null) {
								player.getClientConnection().close(SM_SYSTEM_MESSAGE.STR_KICK_CHARACTER());
								kicked++;
							}
						} catch (Exception ex) {
							log.warn("[CloudControl] Erro ao desconectar jogador {}: {}", player.getName(), ex.getMessage());
						}
					}
					lastKickedPlayersCount.set(kicked);
					restartRemainingSeconds.set(0);
					restartConfirmed.set(true);
					restartCountdownRunning.set(false);
					log.info("[CloudControl] Contagem de 60s encerrada. {} jogador(es) desconectados via kick com seguranca.", kicked);
					return;
				}

				if (remaining == 45 || remaining == 30 || remaining == 15 || remaining == 10 || remaining <= 5) {
					broadcastClientRestartNotice(remaining);
				}

				scheduleNextCountdownTick();
			} catch (Exception e) {
				log.error("[CloudControl] Erro na contagem regressiva de reinicio do client", e);
				restartConfirmed.set(true);
				restartCountdownRunning.set(false);
			}
		}, 1000);
	}

	private void broadcastClientRestartNotice(int seconds) {
		String msg = "ATENÇÃO: O cliente será reiniciado em " + seconds + " segundos. Seus dados serão salvos automaticamente.";
		log.info("[CloudControl] {}", msg);
		PacketSendUtility.broadcastToWorld(new SM_MESSAGE(0, null, msg, ChatType.BRIGHT_YELLOW_CENTER));
		PacketSendUtility.broadcastToWorld(SM_SYSTEM_MESSAGE.STR_SERVER_SHUTDOWN(seconds));
	}

	private static void sendResponse(HttpExchange exchange, int statusCode, String contentType, byte[] data) throws IOException {
		exchange.getResponseHeaders().set("Content-Type", contentType + "; charset=UTF-8");
		exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
		exchange.getResponseHeaders().set("Cache-Control", "no-cache, no-store, must-revalidate");
		exchange.sendResponseHeaders(statusCode, data.length);
		try (OutputStream os = exchange.getResponseBody()) {
			os.write(data);
		}
	}

	private static class RootHandler implements HttpHandler {
		@Override
		public void handle(HttpExchange exchange) throws IOException {
			String uri = exchange.getRequestURI().toString();
			if (uri.contains("today") || uri.contains("notice") || uri.contains("event")) {
				new TodayHandler().handle(exchange);
			} else {
				new ShopHandler().handle(exchange);
			}
		}
	}

	private static class ShopHandler implements HttpHandler {
		@Override
		public void handle(HttpExchange exchange) throws IOException {
			File file = new File("data/web/shop/index.html");
			byte[] content;
			if (file.exists() && file.isFile()) {
				try (FileInputStream fis = new FileInputStream(file)) {
					content = fis.readAllBytes();
				}
			} else {
				content = EmbeddedWebPages.getShopHtml().getBytes(StandardCharsets.UTF_8);
			}
			sendResponse(exchange, 200, "text/html", content);
		}
	}

	private static class TodayHandler implements HttpHandler {
		@Override
		public void handle(HttpExchange exchange) throws IOException {
			File file = new File("data/web/today/index.html");
			byte[] content;
			if (file.exists() && file.isFile()) {
				try (FileInputStream fis = new FileInputStream(file)) {
					content = fis.readAllBytes();
				}
			} else {
				content = EmbeddedWebPages.getTodayHtml().getBytes(StandardCharsets.UTF_8);
			}
			sendResponse(exchange, 200, "text/html", content);
		}
	}

	private class StatusApiHandler implements HttpHandler {
		@Override
		public void handle(HttpExchange exchange) throws IOException {
			int onlinePlayers = World.getInstance().getAllPlayers().size();
			long uptimeSeconds = Math.max(0L, (System.currentTimeMillis() / 1000L) - GameServer.START_TIME_SECONDS);
			boolean countdownActive = restartCountdownRunning.get();
			int remaining = Math.max(0, restartRemainingSeconds.get());
			boolean loginServerUp = com.aionemu.gameserver.network.loginserver.LoginServer.getInstance().isUp();
			boolean chatServerUp = com.aionemu.gameserver.network.chatserver.ChatServer.getInstance().isUp();
			String json = String.format(
				"{\"status\":\"ONLINE\",\"version\":\"5.0 Classic\",\"onlinePlayers\":%d,\"uptimeSeconds\":%d,\"restartCountdownActive\":%s,\"restartRemainingSeconds\":%d,\"allDisconnected\":%s,\"loginServerOnline\":%s,\"chatServerOnline\":%s,\"rates\":{\"exp\":1.0,\"drop\":1.0,\"kinah\":1.0}}",
				onlinePlayers,
				uptimeSeconds,
				countdownActive ? "true" : "false",
				remaining,
				onlinePlayers == 0 ? "true" : "false",
				loginServerUp ? "true" : "false",
				chatServerUp ? "true" : "false"
			);
			sendResponse(exchange, 200, "application/json", json.getBytes(StandardCharsets.UTF_8));
		}
	}

	private class SafeClientRestartHandler implements HttpHandler {
		@Override
		public void handle(HttpExchange exchange) throws IOException {
			int onlinePlayers = World.getInstance().getAllPlayers().size();
			if (onlinePlayers <= 0 && !restartCountdownRunning.get()) {
				restartConfirmed.set(true);
				restartRemainingSeconds.set(0);
				String json = "{\"status\":\"READY_TO_RESTART\",\"onlinePlayers\":0,\"remainingSeconds\":0,\"allDisconnected\":true,\"confirmed\":true,\"kickedPlayers\":0,\"message\":\"Nenhum jogador online. Reinício imediato confirmado.\"}";
				sendResponse(exchange, 200, "application/json", json.getBytes(StandardCharsets.UTF_8));
				return;
			}

			int delaySeconds = 60;
			String query = exchange.getRequestURI().getQuery();
			if (query != null && query.contains("seconds=")) {
				for (String part : query.split("&")) {
					if (part.startsWith("seconds=")) {
						try {
							delaySeconds = Math.max(1, Math.min(300, Integer.parseInt(part.substring("seconds=".length()))));
						} catch (NumberFormatException ignored) {
						}
					}
				}
			}

			startClientRestartCountdown(delaySeconds);
			int rem = Math.max(0, restartRemainingSeconds.get());
			String json = String.format(
				"{\"status\":\"COUNTDOWN_ACTIVE\",\"onlinePlayers\":%d,\"remainingSeconds\":%d,\"allDisconnected\":false,\"confirmed\":false,\"message\":\"Aviso enviado na tela para %d jogador(es). Contagem de %ds iniciada no ThreadPoolManager.\"}",
				onlinePlayers, rem, onlinePlayers, rem
			);
			sendResponse(exchange, 200, "application/json", json.getBytes(StandardCharsets.UTF_8));
		}
	}

	private class SafeClientRestartStatusHandler implements HttpHandler {
		@Override
		public void handle(HttpExchange exchange) throws IOException {
			int onlinePlayers = World.getInstance().getAllPlayers().size();
			boolean active = restartCountdownRunning.get();
			int rem = Math.max(0, restartRemainingSeconds.get());
			boolean confirmed = (!active && onlinePlayers == 0) || restartConfirmed.get();
			String status = confirmed ? "READY_TO_RESTART" : "COUNTDOWN_ACTIVE";
			String json = String.format(
				"{\"status\":\"%s\",\"onlinePlayers\":%d,\"remainingSeconds\":%d,\"allDisconnected\":%s,\"confirmed\":%s,\"kickedPlayers\":%d}",
				status,
				onlinePlayers,
				rem,
				onlinePlayers == 0 ? "true" : "false",
				confirmed ? "true" : "false",
				lastKickedPlayersCount.get()
			);
			sendResponse(exchange, 200, "application/json", json.getBytes(StandardCharsets.UTF_8));
		}
	}
}
