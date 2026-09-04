package com.aionemu.gameserver.services.web;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.services.abyss.AbyssRankingCache;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.mail.MailFormatter;
import com.aionemu.gameserver.services.mail.MailService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.Executors;

/**
 * Servidor Web Integrado do GameServer para o Cliente Classic 5.0 (CEF Browser).
 * Fornece interface nativa HTML5/CSS3 para Aion Shop (Quna/Toll), Rankings de Abyss e Daeva Pass.
 */
public class InGameWebServer {

    private static final Logger log = LoggerFactory.getLogger(InGameWebServer.class);
    private static final InGameWebServer instance = new InGameWebServer();

    public static final int WEB_PORT = 8080;
    private HttpServer server;
    private File webDir;

    public static InGameWebServer getInstance() {
        return instance;
    }

    public synchronized void start() {
        if (server != null) {
            return;
        }
        try {
            webDir = new File("data/web");
            if (!webDir.exists()) {
                webDir.mkdirs();
            }

            server = HttpServer.create(new InetSocketAddress("0.0.0.0", WEB_PORT), 0);
            server.setExecutor(Executors.newCachedThreadPool());

            // Rotas de interface e API
            server.createContext("/", new StaticFileHandler());
            server.createContext("/shop", new ShopPageHandler());
            server.createContext("/ranking", new RankingPageHandler());
            server.createContext("/api/shop/items", new ShopItemsApiHandler());
            server.createContext("/api/shop/buy", new ShopBuyApiHandler());
            server.createContext("/api/ranking/players", new RankingPlayersApiHandler());

            server.start();
            log.info("[InGameWebServer] Servidor Web CEF ativo em http://0.0.0.0:" + WEB_PORT + " (Shop e Rankings)");
        } catch (Exception e) {
            log.warn("[InGameWebServer] Nao foi possivel iniciar na porta " + WEB_PORT + ": " + e.getMessage());
        }
    }

    public synchronized void stop() {
        if (server != null) {
            try {
                server.stop(0);
                server = null;
                log.info("[InGameWebServer] Servidor Web encerrado.");
            } catch (Exception ignored) {
            }
        }
    }

    private static void sendJsonResponse(HttpExchange exchange, int statusCode, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(statusCode, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }

    private static void sendHtmlResponse(HttpExchange exchange, int statusCode, String html) throws IOException {
        byte[] bytes = html.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(statusCode, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }

    private class StaticFileHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String path = exchange.getRequestURI().getPath();
            if (path.equals("/") || path.isEmpty()) {
                path = "/shop.html";
            }
            File file = new File(webDir, path.replace("/", File.separator));
            if (file.exists() && !file.isDirectory()) {
                String contentType = "text/plain";
                if (path.endsWith(".html")) contentType = "text/html; charset=UTF-8";
                else if (path.endsWith(".css")) contentType = "text/css; charset=UTF-8";
                else if (path.endsWith(".js")) contentType = "application/javascript; charset=UTF-8";
                else if (path.endsWith(".png")) contentType = "image/png";
                else if (path.endsWith(".jpg") || path.endsWith(".jpeg")) contentType = "image/jpeg";

                byte[] data = Files.readAllBytes(file.toPath());
                exchange.getResponseHeaders().set("Content-Type", contentType);
                exchange.sendResponseHeaders(200, data.length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(data);
                }
            } else {
                // Fallback para página padrão do Shop
                sendHtmlResponse(exchange, 200, getShopHtmlTemplate());
            }
        }
    }

    private class ShopPageHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            File shopFile = new File(webDir, "shop.html");
            if (shopFile.exists()) {
                byte[] data = Files.readAllBytes(shopFile.toPath());
                exchange.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
                exchange.sendResponseHeaders(200, data.length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(data);
                }
            } else {
                sendHtmlResponse(exchange, 200, getShopHtmlTemplate());
            }
        }
    }

    private class RankingPageHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            File rankFile = new File(webDir, "ranking.html");
            if (rankFile.exists()) {
                byte[] data = Files.readAllBytes(rankFile.toPath());
                exchange.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
                exchange.sendResponseHeaders(200, data.length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(data);
                }
            } else {
                sendHtmlResponse(exchange, 200, getRankingHtmlTemplate());
            }
        }
    }

    private class ShopItemsApiHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            // Catalogo de itens do Quna/Toll Shop
            String json = "[" +
                    "{\"id\":1,\"itemId\":188053000,\"name\":\"Asas da Fenix Ancestral\",\"category\":\"Asas\",\"price\":1200,\"icon\":\"icon_item_wing_phoenix.png\"}," +
                    "{\"id\":2,\"itemId\":188053001,\"name\":\"Traje de Batalha de Beritra\",\"category\":\"Cosmeticos\",\"price\":850,\"icon\":\"icon_item_cloth_suit.png\"}," +
                    "{\"id\":3,\"itemId\":162000029,\"name\":\"Pocao de Recuperacao Maior x100\",\"category\":\"Consumiveis\",\"price\":150,\"icon\":\"icon_item_potion_life.png\"}," +
                    "{\"id\":4,\"itemId\":186000236,\"name\":\"Pergaminho de Teleporte para Sanctum x10\",\"category\":\"Consumiveis\",\"price\":80,\"icon\":\"icon_item_scroll_tp.png\"}," +
                    "{\"id\":5,\"itemId\":190000001,\"name\":\"Pedra de Encantamento Nv. 100 x5\",\"category\":\"Aprimoramento\",\"price\":450,\"icon\":\"icon_item_enchant_stone.png\"}" +
                    "]";
            sendJsonResponse(exchange, 200, json);
        }
    }

    private class ShopBuyApiHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(405, -1);
                return;
            }
            String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            Map<String, String> params = parseFormData(body);
            String charName = params.get("player");
            String itemIdStr = params.get("itemId");
            String priceStr = params.get("price");

            if (charName == null || itemIdStr == null) {
                sendJsonResponse(exchange, 400, "{\"success\":false,\"message\":\"Parametros invalidos.\"}");
                return;
            }

            Player player = World.getInstance().findPlayer(charName);
            if (player == null) {
                sendJsonResponse(exchange, 404, "{\"success\":false,\"message\":\"Jogador deve estar online para receber a compra.\"}");
                return;
            }

            int itemId = Integer.parseInt(itemIdStr);
            int price = priceStr != null ? Integer.parseInt(priceStr) : 0;
            long currentToll = player.getClientConnection().getAccount().getToll();

            if (currentToll < price) {
                sendJsonResponse(exchange, 400, "{\"success\":false,\"message\":\"Saldo de Quna/Toll insuficiente!\"}");
                return;
            }

            // Deduzir Toll e entregar item
            player.getClientConnection().getAccount().setToll(currentToll - price);
            ItemService.addItem(player, itemId, 1);
            PacketSendUtility.sendMessage(player, "[Aion Shop] Compra realizada com sucesso! Item entregue no inventario.");

            sendJsonResponse(exchange, 200, "{\"success\":true,\"message\":\"Compra realizada!\",\"balance\":" + (currentToll - price) + "}");
        }
    }

    private class RankingPlayersApiHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            StringBuilder sb = new StringBuilder("[");
            int rank = 1;
            Iterator<Player> it = World.getInstance().getPlayersIterator();
            boolean first = true;
            while (it.hasNext() && rank <= 50) {
                Player p = it.next();
                if (!first) sb.append(",");
                first = false;
                sb.append(String.format("{\"rank\":%d,\"name\":\"%s\",\"race\":\"%s\",\"playerClass\":\"%s\",\"level\":%d,\"ap\":%d}",
                        rank++, p.getName(), p.getRace().name(), p.getPlayerClass().name(), p.getLevel(), p.getAbyssRank().getAp()));
            }
            sb.append("]");
            sendJsonResponse(exchange, 200, sb.toString());
        }
    }

    private static Map<String, String> parseFormData(String query) {
        Map<String, String> map = new HashMap<>();
        if (query == null || query.isEmpty()) return map;
        String[] pairs = query.split("&");
        for (String pair : pairs) {
            String[] kv = pair.split("=", 2);
            try {
                String k = URLDecoder.decode(kv[0], StandardCharsets.UTF_8.name());
                String v = kv.length > 1 ? URLDecoder.decode(kv[1], StandardCharsets.UTF_8.name()) : "";
                map.put(k, v);
            } catch (Exception ignored) {
            }
        }
        return map;
    }

    public static String getShopHtmlTemplate() {
        return "<!DOCTYPE html>\n" +
                "<html lang=\"pt-BR\">\n" +
                "<head>\n" +
                "    <meta charset=\"UTF-8\">\n" +
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n" +
                "    <title>Aion Classic 5.0 - Quna Shop Oficial</title>\n" +
                "    <style>\n" +
                "        :root { --bg: #0d1117; --panel: rgba(22, 27, 34, 0.85); --accent: #f59e0b; --gold: #fbbf24; --text: #e6edf3; --border: rgba(240, 185, 11, 0.25); }\n" +
                "        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }\n" +
                "        body { background: radial-gradient(circle at top, #1c1917 0%, #0c0a09 100%); color: var(--text); min-height: 100vh; padding: 24px; }\n" +
                "        header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }\n" +
                "        .logo { font-size: 24px; font-weight: bold; color: var(--gold); letter-spacing: 1px; display: flex; align-items: center; gap: 10px; }\n" +
                "        .balance-badge { background: var(--panel); border: 1px solid var(--border); padding: 8px 16px; border-radius: 999px; font-size: 15px; color: var(--gold); font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }\n" +
                "        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }\n" +
                "        .card { background: var(--panel); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; backdrop-filter: blur(8px); }\n" +
                "        .card:hover { transform: translateY(-4px); border-color: var(--gold); box-shadow: 0 8px 24px rgba(245, 158, 11, 0.15); }\n" +
                "        .category { font-size: 12px; color: #a8a29e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }\n" +
                "        .item-name { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 12px; line-height: 1.4; }\n" +
                "        .price-row { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.05); }\n" +
                "        .price { font-size: 18px; font-weight: bold; color: var(--gold); }\n" +
                "        .btn-buy { background: linear-gradient(135deg, #d97706, #f59e0b); color: #000; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: opacity 0.2s; }\n" +
                "        .btn-buy:hover { opacity: 0.9; }\n" +
                "    </style>\n" +
                "</head>\n" +
                "<body>\n" +
                "    <header>\n" +
                "        <div class=\"logo\">✨ AION CLASSIC 5.0 — QUNA STORE</div>\n" +
                "        <div class=\"balance-badge\">🪙 Saldo de Quna: <span id=\"balance\">Disponivel</span></div>\n" +
                "    </header>\n" +
                "    <div class=\"grid\" id=\"item-grid\">\n" +
                "        <!-- Carregado dinamicamente -->\n" +
                "    </div>\n" +
                "    <script>\n" +
                "        fetch('/api/shop/items').then(r => r.json()).then(items => {\n" +
                "            const container = document.getElementById('item-grid');\n" +
                "            container.innerHTML = items.map(it => `\n" +
                "                <div class=\"card\">\n" +
                "                    <div class=\"category\">${it.category}</div>\n" +
                "                    <div class=\"item-name\">${it.name}</div>\n" +
                "                    <div class=\"price-row\">\n" +
                "                        <div class=\"price\">${it.price} Quna</div>\n" +
                "                        <button class=\"btn-buy\" onclick=\"buyItem(${it.itemId}, ${it.price})\">Adquirir</button>\n" +
                "                    </div>\n" +
                "                </div>\n" +
                "            `).join('');\n" +
                "        });\n" +
                "        function buyItem(id, price) {\n" +
                "            const player = prompt('Informe o nome do seu Personagem online:');\n" +
                "            if(!player) return;\n" +
                "            fetch('/api/shop/buy', {\n" +
                "                method: 'POST',\n" +
                "                headers: {'Content-Type': 'application/x-www-form-urlencoded'},\n" +
                "                body: `player=${encodeURIComponent(player)}&itemId=${id}&price=${price}`\n" +
                "            }).then(r => r.json()).then(res => {\n" +
                "                alert(res.message);\n" +
                "                if(res.balance !== undefined) document.getElementById('balance').innerText = res.balance;\n" +
                "            });\n" +
                "        }\n" +
                "    </script>\n" +
                "</body>\n" +
                "</html>";
    }

    public static String getRankingHtmlTemplate() {
        return "<!DOCTYPE html>\n" +
                "<html lang=\"pt-BR\">\n" +
                "<head>\n" +
                "    <meta charset=\"UTF-8\">\n" +
                "    <title>Aion Classic 5.0 - Classificacao do Abyss & PvP</title>\n" +
                "    <style>\n" +
                "        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }\n" +
                "        body { background: #0c0a09; color: #e7e5e4; padding: 24px; }\n" +
                "        h1 { color: #f59e0b; margin-bottom: 20px; font-size: 24px; }\n" +
                "        table { width: 100%; border-collapse: collapse; background: #1c1917; border-radius: 8px; overflow: hidden; }\n" +
                "        th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #292524; }\n" +
                "        th { background: #292524; color: #f59e0b; font-weight: 600; text-transform: uppercase; font-size: 13px; }\n" +
                "        tr:hover { background: #292524; }\n" +
                "        .rank { font-weight: bold; color: #fbbf24; }\n" +
                "    </style>\n" +
                "</head>\n" +
                "<body>\n" +
                "    <h1>🏆 Ranking Oficial de Jogadores (Abyss & Glória)</h1>\n" +
                "    <table>\n" +
                "        <thead>\n" +
                "            <tr>\n" +
                "                <th>#</th>\n" +
                "                <th>Personagem</th>\n" +
                "                <th>Nivel</th>\n" +
                "                <th>Classe</th>\n" +
                "                <th>Faccao</th>\n" +
                "                <th>Pontos Abyss (AP)</th>\n" +
                "            </tr>\n" +
                "        </thead>\n" +
                "        <tbody id=\"rank-body\"></tbody>\n" +
                "    </table>\n" +
                "    <script>\n" +
                "        fetch('/api/ranking/players').then(r => r.json()).then(data => {\n" +
                "            const body = document.getElementById('rank-body');\n" +
                "            body.innerHTML = data.map(p => `\n" +
                "                <tr>\n" +
                "                    <td class=\"rank\">${p.rank}</td>\n" +
                "                    <td><strong>${p.name}</strong></td>\n" +
                "                    <td>${p.level}</td>\n" +
                "                    <td>${p.playerClass}</td>\n" +
                "                    <td>${p.race}</td>\n" +
                "                    <td>${Number(p.ap).toLocaleString()}</td>\n" +
                "                </tr>\n" +
                "            `).join('');\n" +
                "        });\n" +
                "    </script>\n" +
                "</body>\n" +
                "</html>";
    }
}
