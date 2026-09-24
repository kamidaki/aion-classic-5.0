package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0127 (295) - SM_UNK_0127 (20 bytes)
 * Official Classic 5.0: writeH(9) + 9 sequence shorts.
 */
public class SM_UNK_0127 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(9);
        for (int i = 0; i < 9; i++) {
            writeH(i);
        }
    }
}
