package com.aionemu.websocket;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Servidor WebSocket / Management nativo em Java para integracao
 * com o Inicializador Aion Classic - EMU.
 */
public class WebSocketServer {
    private static final Logger log = LoggerFactory.getLogger(WebSocketServer.class);
    private static final int DEFAULT_PORT = 18099;

    private final int port;
    private ServerSocket serverSocket;
    private volatile boolean running = false;
    private final ExecutorService threadPool = Executors.newCachedThreadPool();
    private final Set<ClientConnection> clients = Collections.synchronizedSet(new HashSet<>());

    public WebSocketServer(int port) {
        this.port = port;
    }

    public static void main(String[] args) {
        int p = DEFAULT_PORT;
        if (args.length > 0) {
            try {
                p = Integer.parseInt(args[0]);
            } catch (Exception ignored) {
            }
        }
        WebSocketServer server = new WebSocketServer(p);
        server.start();
    }

    public synchronized void start() {
        if (running) return;
        running = true;
        try {
            serverSocket = new ServerSocket(port);
            log.info("[WebSocketServer] Servidor de Gerenciamento ativo na porta {}", port);

            threadPool.submit(() -> {
                while (running) {
                    try {
                        Socket socket = serverSocket.accept();
                        ClientConnection conn = new ClientConnection(socket, this);
                        clients.add(conn);
                        threadPool.submit(conn);
                    } catch (IOException e) {
                        if (running) {
                            log.error("[WebSocketServer] Erro aceitando conexao: {}", e.getMessage());
                        }
                    }
                }
            });
        } catch (IOException e) {
            log.error("[WebSocketServer] Falha ao iniciar na porta {}: {}", port, e.getMessage());
        }
    }

    public synchronized void stop() {
        running = false;
        try {
            if (serverSocket != null) {
                serverSocket.close();
            }
        } catch (IOException ignored) {
        }
        threadPool.shutdownNow();
        log.info("[WebSocketServer] Servidor de Gerenciamento encerrado.");
    }

    public void broadcast(String message) {
        synchronized (clients) {
            for (ClientConnection c : clients) {
                c.sendTextMessage(message);
            }
        }
    }

    public void removeClient(ClientConnection client) {
        clients.remove(client);
    }

    public static class ClientConnection implements Runnable {
        private final Socket socket;
        private final WebSocketServer server;
        private InputStream in;
        private OutputStream out;
        private boolean isWebSocket = false;

        public ClientConnection(Socket socket, WebSocketServer server) {
            this.socket = socket;
            this.server = server;
        }

        @Override
        public void run() {
            try {
                in = socket.getInputStream();
                out = socket.getOutputStream();

                BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
                String line = reader.readLine();
                if (line == null) {
                    socket.close();
                    return;
                }

                StringBuilder headers = new StringBuilder(line).append("\r\n");
                String secKey = null;
                while ((line = reader.readLine()) != null && !line.isEmpty()) {
                    headers.append(line).append("\r\n");
                    if (line.toLowerCase().startsWith("sec-websocket-key:")) {
                        secKey = line.substring(line.indexOf(':') + 1).trim();
                    }
                }

                if (secKey != null) {
                    // Handshake WebSocket RFC 6455
                    String acceptKey = Base64.getEncoder().encodeToString(
                            MessageDigest.getInstance("SHA-1").digest(
                                    (secKey + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").getBytes(StandardCharsets.UTF_8)
                            )
                    );
                    String response = "HTTP/1.1 101 Switching Protocols\r\n"
                            + "Upgrade: websocket\r\n"
                            + "Connection: Upgrade\r\n"
                            + "Sec-WebSocket-Accept: " + acceptKey + "\r\n\r\n";
                    out.write(response.getBytes(StandardCharsets.UTF_8));
                    out.flush();
                    isWebSocket = true;
                    log.info("[WebSocketServer] Conexao WebSocket aceita de {}", socket.getRemoteSocketAddress());
                } else {
                    // Protocolo HTTP simples fallback
                    String resp = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\":\"ok\",\"service\":\"WebSocketServer\"}";
                    out.write(resp.getBytes(StandardCharsets.UTF_8));
                    out.flush();
                    socket.close();
                    server.removeClient(this);
                    return;
                }

                // Loop de leitura de frames WebSocket
                while (!socket.isClosed()) {
                    int b1 = in.read();
                    if (b1 == -1) break;
                    int b2 = in.read();
                    if (b2 == -1) break;

                    int opcode = b1 & 0x0F;
                    if (opcode == 8) { // Close
                        break;
                    }

                    boolean masked = (b2 & 0x80) != 0;
                    long length = b2 & 0x7F;
                    if (length == 126) {
                        length = ((in.read() << 8) | in.read());
                    } else if (length == 127) {
                        length = 0;
                        for (int i = 0; i < 8; i++) {
                            length = (length << 8) | in.read();
                        }
                    }

                    byte[] masks = new byte[4];
                    if (masked) {
                        in.read(masks);
                    }

                    byte[] payload = new byte[(int) length];
                    int read = 0;
                    while (read < length) {
                        int r = in.read(payload, read, (int) length - read);
                        if (r == -1) break;
                        read += r;
                    }

                    if (masked) {
                        for (int i = 0; i < length; i++) {
                            payload[i] = (byte) (payload[i] ^ masks[i % 4]);
                        }
                    }

                    String text = new String(payload, StandardCharsets.UTF_8);
                    handleMessage(text);
                }
            } catch (Exception e) {
                // Fechamento normal de conexao
            } finally {
                server.removeClient(this);
                try {
                    socket.close();
                } catch (Exception ignored) {
                }
            }
        }

        private void handleMessage(String msg) {
            log.info("[WebSocketServer] Mensagem recebida: {}", msg);
            // Echo / status response
            sendTextMessage("{\"ack\":true,\"echo\":" + msg + "}");
        }

        public synchronized void sendTextMessage(String text) {
            if (!isWebSocket) return;
            try {
                byte[] raw = text.getBytes(StandardCharsets.UTF_8);
                ByteArrayOutputStream frame = new ByteArrayOutputStream();
                frame.write(0x81); // Fin + Opcode 1 (Text)
                if (raw.length <= 125) {
                    frame.write(raw.length);
                } else if (raw.length <= 65535) {
                    frame.write(126);
                    frame.write((raw.length >> 8) & 0xFF);
                    frame.write(raw.length & 0xFF);
                } else {
                    frame.write(127);
                    for (int i = 7; i >= 0; i--) {
                        frame.write((int) ((raw.length >> (8 * i)) & 0xFF));
                    }
                }
                frame.write(raw);
                out.write(frame.toByteArray());
                out.flush();
            } catch (Exception ignored) {
            }
        }
    }
}
