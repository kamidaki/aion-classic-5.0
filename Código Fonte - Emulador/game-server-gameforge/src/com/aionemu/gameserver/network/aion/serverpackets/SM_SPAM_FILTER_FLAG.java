package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SM_SPAM_FILTER_FLAG (Opcode 0x0126 / 294 dec).
 *
 * @author Lost Academy Team & Durak
 */
public class SM_SPAM_FILTER_FLAG extends AionServerPacket {

	private final Player player;

	public SM_SPAM_FILTER_FLAG(Player player) {
		this.player = player;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(this.player != null ? this.player.getObjectId() : 0);
		writeD(0);
	}
}
