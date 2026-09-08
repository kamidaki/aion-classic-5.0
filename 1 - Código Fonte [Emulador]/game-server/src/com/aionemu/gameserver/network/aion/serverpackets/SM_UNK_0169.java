package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0169 (361) - SM_UNK_0169 (12 bytes)
 * Official Classic 5.0 wire: writeH(1) + writeC(1) + writeD(5) + writeH(0) + writeC(0) + writeH(20).
 */
public class SM_UNK_0169 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
        writeC(1);
        writeD(5);
        writeH(0);
        writeC(0);
        writeH(20);
    }
}
