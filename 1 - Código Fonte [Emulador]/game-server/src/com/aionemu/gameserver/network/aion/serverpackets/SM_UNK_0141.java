package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0141 (321) - SM_UNK_0141 (23 bytes)
 * Official Classic 5.0 wire.
 */
public class SM_UNK_0141 extends AionServerPacket {
    private static final byte[] DATA = new byte[] {
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(DATA);
    }
}
