package com.aionemu.chatserver.service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.chatserver.model.ChatClient;
import com.aionemu.chatserver.model.Race;
import com.aionemu.chatserver.model.channel.Channel;
import com.aionemu.chatserver.model.channel.ChatChannels;
import com.aionemu.chatserver.network.aion.serverpackets.SM_CHANNEL_RESPONSE;
import com.aionemu.chatserver.network.aion.serverpackets.SM_PLAYER_AUTH_RESPONSE;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler.ClientChannelHandlerState;
import com.aionemu.commons.utils.Rnd;

/**
 * @author Lost Academy Team & Durak
 */
public class ChatService {

	private static final Logger log = LoggerFactory.getLogger(ChatService.class);
	private static final ChatService instance = new ChatService();
	private final Map<Long, ChatClient> players = new ConcurrentHashMap<>();

	private ChatService() {

	}

	public static ChatService getInstance() {
		return instance;
	}

	public static long makePlayerKey(byte gameServerId, int playerId) {
		return (((long) gameServerId) << 32) | (playerId & 0xFFFFFFFFL);
	}

	public ChatClient registerPlayer(int playerId, String accName, String nick, Race race, byte accessLevel) throws NoSuchAlgorithmException {
		return registerPlayer((byte) 0, playerId, accName, nick, race, accessLevel);
	}

	public ChatClient registerPlayer(byte gameServerId, int playerId, String accName, String nick, Race race, byte accessLevel) throws NoSuchAlgorithmException {
		MessageDigest md = MessageDigest.getInstance("SHA-256");
		md.reset();
		md.update(accName.getBytes(StandardCharsets.UTF_8), 0, accName.length());
		byte[] accountToken = md.digest();
		byte[] token = generateToken(accountToken);
		ChatClient chatClient = new ChatClient(gameServerId, playerId, token, accName, nick, race, accessLevel);
		players.put(makePlayerKey(gameServerId, playerId), chatClient);
		log.info("Registered chat player {} (id={}, GS #{})", nick, playerId, gameServerId);
		return chatClient;
	}

	private byte[] generateToken(byte[] accountToken) {
		byte[] dynamicToken = new byte[16];
		Rnd.nextBytes(dynamicToken);
		byte[] token = new byte[48];
		for (int i = 0; i < token.length; i++) {
			if (i < 16)
				token[i] = dynamicToken[i];
			else
				token[i] = accountToken[i - 16];
		}
		return token;
	}

	public void registerPlayerConnection(int playerId, byte[] token, byte[] identifier, String name, String accName,
		ClientChannelHandler channelHandler) {
		registerPlayerConnection((byte) 0, playerId, token, identifier, name, accName, channelHandler);
	}

	public void registerPlayerConnection(byte gameServerId, int playerId, byte[] token, byte[] identifier, String name, String accName,
		ClientChannelHandler channelHandler) {
		ChatClient chatClient = null;
		if (gameServerId != 0) {
			chatClient = players.get(makePlayerKey(gameServerId, playerId));
		}
		if (chatClient == null) {
			for (ChatClient candidate : players.values()) {
				if (candidate.getClientId() == playerId && candidate.getAccountName().equalsIgnoreCase(accName)) {
					chatClient = candidate;
					break;
				}
			}
		}

		if (chatClient == null)
			log.warn("Client tried to connect but was not yet registered from game server side (id={}, gs={})", playerId, gameServerId);
		else if (!Arrays.equals(chatClient.getToken(), token))
			log.warn("Client tried to connect but given token doesn't match");
		else if (!chatClient.getAccountName().equalsIgnoreCase(accName)) // client sends accName lowercase
			log.warn("Client tried to connect with account name: {} (expected: {})", accName, chatClient.getAccountName());
		else if (!chatClient.getName().equals(name))
			log.warn("Client tried to connect with character name: {} (expected: {})", name, chatClient.getName());
		else {
			chatClient.setIdentifier(identifier);
			chatClient.setChannelHandler(channelHandler);
			channelHandler.sendPacket(new SM_PLAYER_AUTH_RESPONSE());
			channelHandler.setState(ClientChannelHandlerState.AUTHED);
			channelHandler.setChatClient(chatClient);
			BroadcastService.getInstance().addClient(chatClient);
			log.info("Client connected and authenticated to ChatServer: {} on GS #{}", name, chatClient.getGameServerId());
		}
	}

	public void registerPlayerWithChannel(ClientChannelHandler clientChannelHandler, int channelRequestId, String identifier) {
		Channel channel = ChatChannels.getOrCreate(clientChannelHandler.getChatClient(), identifier);
		if (channel != null) {
			clientChannelHandler.getChatClient().addChannel(channel);
			clientChannelHandler.sendPacket(new SM_CHANNEL_RESPONSE(channel, channelRequestId));
		}
	}

	public void playerLogout(int playerId) {
		playerLogout((byte) 0, playerId);
	}

	public void playerLogout(byte gameServerId, int playerId) {
		ChatClient chatClient = null;
		if (gameServerId != 0) {
			chatClient = players.remove(makePlayerKey(gameServerId, playerId));
		}
		if (chatClient == null) {
			for (Map.Entry<Long, ChatClient> entry : players.entrySet()) {
				if (entry.getValue().getClientId() == playerId) {
					chatClient = players.remove(entry.getKey());
					break;
				}
			}
		}
		if (chatClient != null) {
			BroadcastService.getInstance().removeClient(chatClient);
			log.info("Player[id={}, gs={}] logged out", playerId, chatClient.getGameServerId());
			if (chatClient.getChannelHandler() != null)
				chatClient.getChannelHandler().close();
			else
				log.warn("Received logout event without client authentication for player {}", playerId);
		}
	}

	public void gagPlayer(int playerId, long gagTimeMillis) {
		gagPlayer((byte) 0, playerId, gagTimeMillis);
	}

	public void gagPlayer(byte gameServerId, int playerId, long gagTimeMillis) {
		ChatClient client = null;
		if (gameServerId != 0) {
			client = players.get(makePlayerKey(gameServerId, playerId));
		}
		if (client == null) {
			for (ChatClient candidate : players.values()) {
				if (candidate.getClientId() == playerId) {
					client = candidate;
					break;
				}
			}
		}
		if (client != null) {
			client.setGagTime(gagTimeMillis);
			log.info("Player[id={}, gs={}] was gagged for {} minutes", playerId, client.getGameServerId(), gagTimeMillis / 60000);
		}
	}

	public void onGameServerDisconnect(byte gameServerId) {
		java.util.List<Long> toRemove = new java.util.ArrayList<>();
		for (Map.Entry<Long, ChatClient> entry : players.entrySet()) {
			if (entry.getValue().getGameServerId() == gameServerId) {
				toRemove.add(entry.getKey());
			}
		}
		for (Long key : toRemove) {
			ChatClient client = players.remove(key);
			if (client != null) {
				BroadcastService.getInstance().removeClient(client);
				if (client.getChannelHandler() != null) {
					client.getChannelHandler().close();
				}
			}
		}
		log.info("Cleaned up {} chat clients for disconnected GameServer #{}", toRemove.size(), gameServerId);
	}
}
