package com.aionemu.chatserver.service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.chatserver.configs.network.NetworkConfig;
import com.aionemu.chatserver.network.gameserver.GsAuthResponse;
import com.aionemu.chatserver.network.gameserver.GsConnection;

/**
 * @author Lost Academy Team & Durak
 */
public class GameServerService {

	private static final Logger log = LoggerFactory.getLogger(GameServerService.class);
	private static final GameServerService instance = new GameServerService();
	private final Map<Byte, GsConnection> registeredServers = new ConcurrentHashMap<>();

	public static GameServerService getInstance() {
		return instance;
	}

	public GsAuthResponse registerGameServer(GsConnection connection, byte gameServerId, String password) {
		if (!password.equals(NetworkConfig.GAMESERVER_PASSWORD))
			return GsAuthResponse.NOT_AUTHED;

		GsConnection existing = registeredServers.get(gameServerId);
		if (existing != null && existing.getState() == GsConnection.GameServerConnectionState.AUTHED) {
			return GsAuthResponse.ALREADY_REGISTERED;
		}

		registeredServers.put(gameServerId, connection);
		connection.setGameServerId(gameServerId);
		log.info("Gameserver #{} registered successfully in ChatServer", gameServerId);
		return GsAuthResponse.AUTHED;
	}

	public void setOffline(byte gameServerId) {
		registeredServers.remove(gameServerId);
		ChatService.getInstance().onGameServerDisconnect(gameServerId);
		log.info("Gameserver #{} is disconnected from ChatServer", gameServerId);
	}

	public boolean isGameServerOnline(byte gameServerId) {
		return registeredServers.containsKey(gameServerId);
	}
}
