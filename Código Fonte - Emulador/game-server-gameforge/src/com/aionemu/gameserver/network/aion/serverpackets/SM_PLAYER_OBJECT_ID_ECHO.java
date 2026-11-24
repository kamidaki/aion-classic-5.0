package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0146 (326) - SM_PLAYER_OBJECT_ID_ECHO (8 bytes)
 * Official Classic 5.0 player object ID echo notification.
 * Dispatched on world entry handshake right after bind point and channel info.
 * Wire: writeD(objectId) + writeD(0).
 */
public class SM_PLAYER_OBJECT_ID_ECHO extends AionServerPacket {
	private final int objectId;

	public SM_PLAYER_OBJECT_ID_ECHO() {
		this(0);
	}

	public SM_PLAYER_OBJECT_ID_ECHO(int objectId) {
		this.objectId = objectId;
	}

	public int getObjectId() {
		return objectId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeD(0);
	}
}
