package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01BA (442) - SM_REGION_CHAT_CHANNEL_INFO (3 bytes)
 * Region chat channel availability flags.
 */
public class SM_REGION_CHAT_CHANNEL_INFO extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
        writeC(0);
    }
}
