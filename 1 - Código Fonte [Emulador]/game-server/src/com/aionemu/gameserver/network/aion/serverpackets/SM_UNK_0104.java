package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0104 (260) - SM_UNK_0104 (212 bytes)
 * Canonical payload extracted from official Classic 5.0 PCAP.
 */
public class SM_UNK_0104 extends AionServerPacket {
    private static final byte[] BASELINE = new byte[] {
        (byte) 0xEA, (byte) 0xF6, 26, (byte) 0xC0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
        15, 0, 106, (byte) 0xE3, (byte) 0xF5, 5, 1, 0, 0, 0, 0, 0, 15, 1, 1, (byte) 0x82,
        105, (byte) 0xF7, 5, 1, 0, 0, 0, 0, 0, 15, 1, 2, (byte) 0x8D, (byte) 0xF0, (byte) 0xF8, 5,
        1, 0, 0, 0, 0, 0, 15, 1, 3, (byte) 0xFF, (byte) 0x83, (byte) 0xFD, 5, 1, 0, 0,
        0, 0, 0, 15, 1, 4, (byte) 0xC0, 10, (byte) 0xFF, 5, 1, 0, 0, 0, 0, 0,
        15, 1, 5, 123, (byte) 0x9E, 3, 6, 1, 0, 0, 0, 0, 0, 15, 1, 6,
        (byte) 0xF0, (byte) 0xB8, 9, 6, 1, 0, 0, 0, 0, 0, 15, 1, 7, 65, (byte) 0xC6, 12,
        6, 1, 0, 0, 0, 0, 0, 15, 1, 8, (byte) 0x8E, (byte) 0xD3, 15, 6, 1, 0,
        0, 0, 0, 0, 15, 1, 9, (byte) 0xDA, 88, 17, 6, 1, 0, 0, 0, 0,
        0, 15, 1, 10, 84, (byte) 0x80, 26, 6, 1, 0, 0, 0, 0, 0, 15, 1,
        11, 7, 7, 28, 6, 1, 0, 0, 0, 0, 0, 15, 1, 12, (byte) 0xF3, (byte) 0x8D,
        29, 6, 1, 0, 0, 0, 0, 0, 15, 1, 13, 122, 20, 31, 6, 1,
        0, 0, 0, 0, 0, 15, 1, 14, (byte) 0xBD, (byte) 0xC5, (byte) 0xDA, 6, 1, 0, 0, 0,
        0, 0, 15, 1
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(BASELINE);
    }
}
