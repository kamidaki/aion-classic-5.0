package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0181 (385) - SM_UNK_0181 (38 bytes)
 * Canonical payload extracted from official Classic 5.0 PCAP.
 */
public class SM_UNK_0181 extends AionServerPacket {
    private static final byte[] BASELINE = new byte[] {
        1, 0, 124, 98, 3, 0, 40, (byte) 0x8B, 12, (byte) 0x80, (byte) 0xFD, 105, 2, 0, (byte) 0xFD, 105,
        2, 0, 76, 54, (byte) 0x90, 106, 0, 0, 0, 0, 62, 102, 24, 69, 107, 20,
        (byte) 0xB8, 68, (byte) 0xD9, 12, 106, 67
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(BASELINE);
    }
}
