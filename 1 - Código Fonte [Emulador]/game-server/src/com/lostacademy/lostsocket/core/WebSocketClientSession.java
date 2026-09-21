package com.lostacademy.lostsocket.core;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * RFC 6455 compliant WebSocket client session handler running in a Virtual Thread.
 * Enforces mandatory X-Token security check before upgrading connection.
 */
public class WebSocketClientSession implements Runnable {

	private static final Logger log = LoggerFactory.getLogger(WebSocketClientSession.class);
	private static final String WS_MAGIC_KEY = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

	private final Socket socket;
	private final String expectedToken;
	private final WebSocketServer server;
	private final AtomicBoolean closed = new AtomicBoolean(false);
	private final Object sendLock = new Object();

	private InputStream in;
	private OutputStream out;
	private volatile boolean authenticated = false;

	public WebSocketClientSession(Socket socket, String expectedToken, WebSocketServer server) {
		this.socket = socket;
		this.expectedToken = expectedToken;
		this.server = server;
	}

	@Override
	public void run() {
		try {
			socket.setSoTimeout(5000); // 5s handshake timeout
			in = socket.getInputStream();
			out = socket.getOutputStream();

			// Read HTTP request header
			byte[] headerBuffer = new byte[4096];
			int headerLen = 0;
			while (headerLen < headerBuffer.length) {
				int b = in.read();
				if (b == -1) break;
				headerBuffer[headerLen++] = (byte) b;
				if (headerLen >= 4 &&
					headerBuffer[headerLen - 4] == '\r' &&
					headerBuffer[headerLen - 3] == '\n' &&
					headerBuffer[headerLen - 2] == '\r' &&
					headerBuffer[headerLen - 1] == '\n') {
					break;
				}
			}

			String requestHeader = new String(headerBuffer, 0, headerLen, StandardCharsets.UTF_8);

			// Validate Security Token
			if (expectedToken != null && !expectedToken.isEmpty()) {
				String expectedHeader = "X-Token: " + expectedToken;
				if (!requestHeader.contains(expectedHeader)) {
					log.warn("[BrSocket] Rejeitado cliente sem token valido de {}: {}", socket.getInetAddress(), requestHeader);
					out.write("HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n\r\nInvalid Security Token\r\n".getBytes(StandardCharsets.UTF_8));
					out.flush();
					close();
					return;
				}
			}

			// Validate WebSocket Upgrade
			Matcher keyMatcher = Pattern.compile("Sec-WebSocket-Key:\\s*([^\\r\\n]+)", Pattern.CASE_INSENSITIVE).matcher(requestHeader);
			if (!keyMatcher.find()) {
				out.write("HTTP/1.1 400 Bad Request\r\n\r\n".getBytes(StandardCharsets.UTF_8));
				out.flush();
				close();
				return;
			}

			String clientKey = keyMatcher.group(1).trim();
			String acceptKey = Base64.getEncoder().encodeToString(
				MessageDigest.getInstance("SHA-1").digest((clientKey + WS_MAGIC_KEY).getBytes(StandardCharsets.UTF_8))
			);

			String response = "HTTP/1.1 101 Switching Protocols\r\n" +
				"Upgrade: websocket\r\n" +
				"Connection: Upgrade\r\n" +
				"Sec-WebSocket-Accept: " + acceptKey + "\r\n\r\n";

			out.write(response.getBytes(StandardCharsets.UTF_8));
			out.flush();

			socket.setSoTimeout(0); // Persistent connection for telemetry
			authenticated = true;
			server.registerSession(this);

			log.info("[BrSocket] Cliente BrService autenticado e conectado com sucesso de {}", socket.getRemoteSocketAddress());

			// Send welcome packet
			sendText("{\"type\":\"AUTH_OK\",\"message\":\"BrService Telemetry Connected\",\"port\":" + socket.getPort() + "}");

			// Message loop
			byte[] frameHeader = new byte[2];
			while (!closed.get()) {
				if (!readFully(in, frameHeader, 0, 2)) break;
				int opcode = frameHeader[0] & 0x0F;
				boolean masked = (frameHeader[1] & 0x80) != 0;
				long payloadLen = frameHeader[1] & 0x7F;

				if (payloadLen == 126) {
					byte[] extLen = new byte[2];
					if (!readFully(in, extLen, 0, 2)) break;
					payloadLen = ((extLen[0] & 0xFF) << 8) | (extLen[1] & 0xFF);
				} else if (payloadLen == 127) {
					byte[] extLen = new byte[8];
					if (!readFully(in, extLen, 0, 8)) break;
					payloadLen = 0;
					for (int i = 0; i < 8; i++) {
						payloadLen = (payloadLen << 8) | (extLen[i] & 0xFF);
					}
				}

				byte[] maskKey = new byte[4];
				if (masked) {
					if (!readFully(in, maskKey, 0, 4)) break;
				}

				byte[] payload = new byte[(int) Math.min(payloadLen, 65536)];
				if (!readFully(in, payload, 0, payload.length)) break;

				if (masked) {
					for (int i = 0; i < payload.length; i++) {
						payload[i] ^= maskKey[i % 4];
					}
				}

				if (opcode == 0x8) { // Close frame
					break;
				} else if (opcode == 0x9) { // Ping
					sendControlFrame(0xA, payload); // Pong
				} else if (opcode == 0x1) { // Text frame
					String msg = new String(payload, StandardCharsets.UTF_8);
					handleIncomingMessage(msg);
				}
			}

		} catch (Exception e) {
			// Normal socket close or network reset
		} finally {
			close();
		}
	}

	private void handleIncomingMessage(String msg) {
		if (msg == null || msg.isEmpty()) return;
		try {
			if (msg.contains("SET_COMBO_VISIBILITY")) {
				boolean visible = msg.contains("\"visible\":true") || msg.contains(":1") || msg.endsWith("1");
				boolean hidden = !visible;
				com.lostacademy.lostsocket.combat.ComboService.getInstance().setGlobalComboHidden(hidden);
				for (var player : com.aionemu.gameserver.world.World.getInstance().getAllPlayers()) {
					if (player != null && player.isOnline()) {
						com.lostacademy.lostsocket.combat.ComboService.getInstance().setComboUiHidden(player.getObjectId(), hidden);
					}
				}
				log.info("[BrSocket] Atualizado status de exibicao do Combo UI para: visible={}", visible);
			}
		} catch (Exception e) {
			log.error("[BrSocket] Erro ao processar mensagem recebida: {}", msg, e);
		}
	}

	public void sendText(String text) {
		if (closed.get() || !authenticated) return;
		try {
			byte[] rawData = text.getBytes(StandardCharsets.UTF_8);
			int frameCount;
			byte[] frame = new byte[10];

			frame[0] = (byte) 0x81; // FIN + Text opcode
			if (rawData.length <= 125) {
				frame[1] = (byte) rawData.length;
				frameCount = 2;
			} else if (rawData.length <= 65535) {
				frame[1] = (byte) 126;
				frame[2] = (byte) ((rawData.length >> 8) & 0xFF);
				frame[3] = (byte) (rawData.length & 0xFF);
				frameCount = 4;
			} else {
				frame[1] = (byte) 127;
				for (int i = 0; i < 8; i++) {
					frame[2 + i] = (byte) ((rawData.length >> ((7 - i) * 8)) & 0xFF);
				}
				frameCount = 10;
			}

			byte[] reply = new byte[frameCount + rawData.length];
			System.arraycopy(frame, 0, reply, 0, frameCount);
			System.arraycopy(rawData, 0, reply, frameCount, rawData.length);

			synchronized (sendLock) {
				if (closed.get() || out == null) return;
				out.write(reply);
				out.flush();
			}
		} catch (Exception e) {
			close();
		}
	}

	private void sendControlFrame(int opcode, byte[] payload) {
		try {
			byte[] reply = new byte[2 + (payload != null ? payload.length : 0)];
			reply[0] = (byte) (0x80 | (opcode & 0x0F));
			reply[1] = (byte) (payload != null ? payload.length : 0);
			if (payload != null && payload.length > 0) {
				System.arraycopy(payload, 0, reply, 2, payload.length);
			}
			synchronized (sendLock) {
				if (closed.get() || out == null) return;
				out.write(reply);
				out.flush();
			}
		} catch (Exception ignored) {
			close();
		}
	}

	public void close() {
		if (closed.compareAndSet(false, true)) {
			server.unregisterSession(this);
			try {
				if (in != null) in.close();
				if (out != null) out.close();
				if (socket != null && !socket.isClosed()) socket.close();
			} catch (Exception ignored) {}
			log.info("[BrSocket] Sessao encerrada para {}", socket.getRemoteSocketAddress());
		}
	}

	private static boolean readFully(InputStream in, byte[] b, int off, int len) throws Exception {
		int total = 0;
		while (total < len) {
			int r = in.read(b, off + total, len - total);
			if (r == -1) return false;
			total += r;
		}
		return true;
	}
}
