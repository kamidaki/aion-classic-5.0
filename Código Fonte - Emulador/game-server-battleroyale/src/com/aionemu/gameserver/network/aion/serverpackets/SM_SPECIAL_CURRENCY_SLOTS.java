package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x005F (95) - SM_SPECIAL_CURRENCY_SLOTS (134 bytes)
 * Special currency / token slot table baseline.
 */
public class SM_SPECIAL_CURRENCY_SLOTS extends AionServerPacket {
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
