package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SM_CHANNEL_CHATTING_BLACKLIST_SETTING (Opcode 0x012C / 300 dec).
 *
 * @author Lost Academy Team & Durak
 */
public class SM_CHANNEL_CHATTING_BLACKLIST_SETTING extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(1); // 1 em toda entrada oficial (aionlook.pcapng e subida-1-60)
	}
}
