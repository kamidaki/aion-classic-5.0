package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0151 (337) - SM_UNK_0151 (6 bytes)
 * Official Classic 5.0 wire: writeD(0) + writeH(0).
 */
public class SM_UNK_0151 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0);
        writeH(0);
    }
}
