package com.aionemu.chatserver.network.aion.clientpackets;

import java.nio.charset.StandardCharsets;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.network.aion.AbstractClientPacket;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;
import com.aionemu.chatserver.service.ChatService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_PLAYER_AUTH extends AbstractClientPacket {

	private int playerId;
	private byte[] token;
	private byte[] identifier;
	private String identifierSeparator;
	private String accountName;

	public CM_PLAYER_AUTH(ByteBuf channelBuffer, ClientChannelHandler clientChannelHandler, byte opCode) {
		super(channelBuffer, clientChannelHandler, opCode);
	}

	@Override
	protected void readImpl() {
		identifierSeparator = new String(readB(2), StandardCharsets.UTF_16LE); // @
		readC(); // 0
		readD(); // 1
		int gameNameLength = readH() * 2;
		readB(gameNameLength); // AION
		readD(); // 27
		readD(); // 1 or 3
		readD(); // 0
		playerId = readD();
		readD(); // 0
		readD(); // 0
		readD(); // 0
		int length = readH() * 2;
		identifier = readB(length);
		int accountNameLength = readH() * 2;
		accountName = new String(readB(accountNameLength), StandardCharsets.UTF_16LE);
		int tokenLength = readH();
		token = readB(tokenLength);
	}

	@Override
	protected void runImpl() {
		if (identifier == null || identifier.length == 0) {
			return;
		}
		String nameIdentifier = new String(identifier, StandardCharsets.UTF_16LE); // Name@identifier
		int sepIndex = identifierSeparator != null ? nameIdentifier.lastIndexOf(identifierSeparator) : -1;
		String charName = sepIndex >= 0 ? nameIdentifier.substring(0, sepIndex) : nameIdentifier;
		// Classic 5.0 client sends account name with "_sd_" prefix; strip it before comparison
		String cleanAccountName = (accountName != null && accountName.startsWith("_sd_")) ? accountName.substring(4) : (accountName != null ? accountName : "");
		ChatService.getInstance().registerPlayerConnection(playerId, token, identifier, charName, cleanAccountName, clientChannelHandler);
	}
}
