package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0110 (272) - SM_UNK_0110 (36 bytes)
 * Canonical payload extracted from official Classic 5.0 PCAP.
 */
public class SM_UNK_0110 extends AionServerPacket {
    private static final byte[] BASELINE = new byte[] {
        1, 0, 88, 109, 32, 15, 0, 0, 0, 0, 2, 1, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 1
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(BASELINE);
    }
}
