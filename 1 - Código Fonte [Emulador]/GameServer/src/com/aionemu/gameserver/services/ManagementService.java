package com.aionemu.gameserver.services;

import com.aionemu.gameserver.ShutdownHook;
import com.aionemu.gameserver.ShutdownHook.ShutdownMode;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import java.util.concurrent.Executors;

/**
 * Servico de Gerenciamento e Telemetria Local para o Inicializador Aion Classic - EMU.
 * Porta padrao: 127.0.0.1:18091 (Apenas conexoes locais autorizadas)
 */
public class ManagementService {
    private static final Logger log = LoggerFactory.getLogger(ManagementService.class);
    private static final int MANAGEMENT_PORT = 18091;
    private static final ManagementService instance = new ManagementService();

    private HttpServer server;
    private final long startTime = System.currentTimeMillis();

    public static ManagementService getInstance() {
        return instance;
    }

    public synchronized void start() {
        if (server != null) {
            return;
        }
        try {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", MANAGEMENT_PORT), 0);
            server.setExecutor(Executors.newCachedThreadPool());

            server.createContext("/status", new StatusHandler());
            server.createContext("/shutdown", new ShutdownHandler());
            server.createContext("/announce", new AnnounceHandler());

            server.start();
            log.info("[ManagementService] Servico de controle local ativo em 127.0.0.1:" + MANAGEMENT_PORT);
        } catch (IOException e) {
            log.warn("[ManagementService] Nao foi possivel iniciar na porta " + MANAGEMENT_PORT + ": " + e.getMessage());
        }
    }

    public synchronized void stop() {
        if (server != null) {
            try {
                server.stop(0);
                server = null;
            } catch (Exception ignored) {
            }
        }
    }

    private class StatusHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(405, -1);
                return;
            }
            int onlinePlayers = 0;
            Iterator<Player> it = World.getInstance().getPlayersIterator();
            while (it.hasNext()) {
                it.next();
                onlinePlayers++;
            }
            long uptimeSecs = (System.currentTimeMillis() - startTime) / 1000;
            String json = String.format("{\"status\":\"online\",\"server\":\"GameServer\",\"players\":%d,\"uptime_seconds\":%d}",
                    onlinePlayers, uptimeSecs);
            byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
            exchange.sendResponseHeaders(200, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        }
    }

    private class ShutdownHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(405, -1);
                return;
            }

            StringBuilder body = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    body.append(line);
                }
            }

            String content = body.toString().toLowerCase();
            int delay = 60;
            boolean restart = content.contains("restart");

            // Extrai delay se presente
            if (content.contains("delay")) {
                try {
                    String[] parts = content.split("delay");
                    if (parts.length > 1) {
                        String numPart = parts[1].replaceAll("[^0-9]", " ").trim().split("\\s+")[0];
                        delay = Integer.parseInt(numPart);
                        if (delay < 1) delay = 1;
                        if (delay > 600) delay = 600;
                    }
                } catch (Exception ignored) {
                }
            }

            final int finalDelay = delay;
            final ShutdownMode mode = restart ? ShutdownMode.RESTART : ShutdownMode.SHUTDOWN;

            log.info("[ManagementService] Recebido comando de desligamento seguro: modo=" + mode.getText() + ", delay=" + finalDelay + "s");

            new Thread(() -> {
                try {
                    ShutdownHook.getInstance().doShutdown(finalDelay, 1, mode);
                } catch (Exception e) {
                    log.error("[ManagementService] Erro executando doShutdown: " + e.getMessage(), e);
                }
            }, "Management-Shutdown-Thread").start();

            String response = String.format("{\"status\":\"shutting_down\",\"delay\":%d,\"mode\":\"%s\"}", finalDelay, mode.getText());
            byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
            exchange.sendResponseHeaders(200, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        }
    }

    private class AnnounceHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(405, -1);
                return;
            }

            StringBuilder body = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    body.append(line);
                }
            }

            String message = body.toString();
            if (message.contains("message")) {
                int idx = message.indexOf("message");
                message = message.substring(idx + 7).replaceAll("[\"\\}:]", "").trim();
            }

            if (!message.isEmpty()) {
                final String finalMsg = message;
                World.getInstance().doOnAllPlayers(player -> {
                    PacketSendUtility.sendBrightYellowMessageOnCenter(player, "[Anúncio] " + finalMsg);
                });
            }

            String response = "{\"status\":\"ok\"}";
            byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
            exchange.sendResponseHeaders(200, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        }
    }
}
