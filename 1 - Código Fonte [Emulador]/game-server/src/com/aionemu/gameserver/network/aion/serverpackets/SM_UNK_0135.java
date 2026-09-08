package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0135 (309) - SM_UNK_0135 (19 bytes)
 * Official Classic 5.0 wire: 67 00 00 00 01 02 4b 00 00 00 4b 00 00 00 00 00 00 00 00
 */
public class SM_UNK_0135 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0x67);
        writeC(1);
        writeC(2);
        writeD(0x4B);
        writeD(0x4B);
        writeD(0);
        writeC(0);
    }
}
