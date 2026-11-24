package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SM_CHAT_ACCUSE (Opcode 0x0121 / 289 dec).
 *
 * @author Lost Academy Team & Durak
 */
public class SM_CHAT_ACCUSE extends AionServerPacket {

	private final Player player;

	public SM_CHAT_ACCUSE(Player player) {
		this.player = player;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(this.player != null ? this.player.getObjectId() : 0);
		writeC(0);
	}
}
