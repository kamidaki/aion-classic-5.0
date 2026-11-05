package com.aionemu.chatserver.network.gameserver.clientpackets;

import java.nio.ByteBuffer;

import com.aionemu.chatserver.network.gameserver.GsClientPacket;
import com.aionemu.chatserver.network.gameserver.GsConnection;
import com.aionemu.chatserver.service.ChatService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_PLAYER_GAG extends GsClientPacket {

	private int playerId;
	private long gagTimeMillis;

	public CM_PLAYER_GAG(ByteBuffer buf, GsConnection connection) {
		super(buf, connection, 0x03);
	}

	@Override
	protected void readImpl() {
		playerId = readD();
		gagTimeMillis = readQ();
	}

	@Override
	protected void runImpl() {
		byte gsId = getConnection().getGameServerId();
		ChatService.getInstance().gagPlayer(gsId, playerId, gagTimeMillis);
	}
}
