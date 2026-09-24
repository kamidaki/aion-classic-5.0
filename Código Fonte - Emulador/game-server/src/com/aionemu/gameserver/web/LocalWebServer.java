package com.aionemu.gameserver.web;

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
import java.util.concurrent.Executors;

/**
 * Servidor Web Local Integrado para Aion Shop (Black Cloud Marketplace) e Aion Today.
 * Elimina qualquer dependência de servidores externos ou páginas coreanas/oficiais.
 */
public class LocalWebServer {

	private static final Logger log = LoggerFactory.getLogger(LocalWebServer.class);
	private static final LocalWebServer instance = new LocalWebServer();

	private HttpServer server;
	private final int port = 8080;

	public static LocalWebServer getInstance() {
		return instance;
	}

	public synchronized void start(int portToUse) {
		if (server != null) {
			return;
		}
		try {
			int targetPort = (portToUse > 0) ? portToUse : port;
			server = HttpServer.create(new InetSocketAddress(targetPort), 0);
			server.setExecutor(Executors.newFixedThreadPool(4));

			server.createContext("/", new RootHandler());
			server.createContext("/shop", new ShopHandler());
			server.createContext("/today", new TodayHandler());
			server.createContext("/api/status", new StatusApiHandler());

			server.start();
			log.info("LocalWebServer iniciado com sucesso na porta http://127.0.0.1:{}", targetPort);
		} catch (IOException e) {
			log.warn("Nao foi possivel iniciar LocalWebServer na porta {}: {}", portToUse, e.getMessage());
		}
	}

	public synchronized void stop() {
		if (server != null) {
			server.stop(0);
			server = null;
			log.info("LocalWebServer finalizado.");
		}
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

	private static class StatusApiHandler implements HttpHandler {
		@Override
		public void handle(HttpExchange exchange) throws IOException {
			String json = "{\"status\":\"ONLINE\",\"version\":\"5.0 Classic\",\"rates\":{\"exp\":1.0,\"drop\":1.0,\"kinah\":1.0}}";
			sendResponse(exchange, 200, "application/json", json.getBytes(StandardCharsets.UTF_8));
		}
	}
}
