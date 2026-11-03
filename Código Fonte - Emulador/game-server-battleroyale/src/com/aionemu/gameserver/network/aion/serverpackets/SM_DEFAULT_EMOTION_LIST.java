package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x00BC (188) - SM_DEFAULT_EMOTION_LIST (2 bytes)
 * Handshake for default emotion / animation list.
 */
public class SM_DEFAULT_EMOTION_LIST extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
    }
}
