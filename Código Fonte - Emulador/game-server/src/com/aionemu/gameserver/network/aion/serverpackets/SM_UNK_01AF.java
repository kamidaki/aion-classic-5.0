package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01AF (431) - SM_UNK_01AF (5 bytes)
 * Official Classic 5.0 wire: writeD(0) + writeC(0).
 */
public class SM_UNK_01AF extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0);
        writeC(0);
    }
}
