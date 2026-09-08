package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0159 (345) - SM_UNK_0159 (66 bytes)
 * Canonical payload extracted from official Classic 5.0 PCAP.
 */
public class SM_UNK_0159 extends AionServerPacket {
    private static final byte[] BASELINE = new byte[] {
        8, 0, 7, 0, 0, 0, 3, 0, 0, 0, 8, 0, 0, 0, 5, 0,
        0, 0, 9, 0, 0, 0, 20, 0, 0, 0, 10, 0, 0, 0, 1, 0,
        0, 0, 11, 0, 0, 0, 10, 0, 0, 0, 12, 0, 0, 0, 1, 0,
        0, 0, 14, 0, 0, 0, 1, 0, 0, 0, 15, 0, 0, 0, 2, 0,
        0, 0
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(BASELINE);
    }
}
