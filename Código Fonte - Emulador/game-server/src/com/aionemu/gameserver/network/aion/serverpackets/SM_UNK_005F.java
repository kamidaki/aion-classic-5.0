package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x005F (95) - SM_UNK_005F (134 bytes)
 * Canonical payload extracted from official Classic 5.0 PCAP.
 */
public class SM_UNK_005F extends AionServerPacket {
    private static final byte[] BASELINE = new byte[] {
        11, 0, (byte) 0xC3, 11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (byte) 0xC4, 11,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (byte) 0xC5, 11, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, (byte) 0xC6, 11, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, (byte) 0xC7, 11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (byte) 0xC8, 11,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (byte) 0xC9, 11, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, (byte) 0xCD, 11, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, (byte) 0xCE, 11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (byte) 0xCF, 11,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 39, 12, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(BASELINE);
    }
}
