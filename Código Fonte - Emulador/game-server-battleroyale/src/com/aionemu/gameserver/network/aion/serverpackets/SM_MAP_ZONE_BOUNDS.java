package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01AC (428) - SM_MAP_ZONE_BOUNDS (254 bytes)
 * Canonical active map zone boundary table.
 */
public class SM_MAP_ZONE_BOUNDS extends AionServerPacket {
    private static final byte[] BASELINE = new byte[] {
        1, 0, 0, 0, 0, 0, 0, 0, 23, 0, 0, 0, 60, 0, (byte) 0x9F, 4,
        0, 46, 19, 15, 0, 46, (byte) 0xA0, 15, 0, 46, 45, 17, 0, 46, 118, 17,
        0, 46, 25, 28, 0, 46, 98, 34, 0, 46, (byte) 0xF9, 35, 0, 46, 50, 45,
        0, 46, (byte) 0xD8, 48, 0, 46, (byte) 0xB3, 54, 0, 46, (byte) 0xCA, 60, 0, 46, (byte) 0xFB, (byte) 0x99,
        0, 46, (byte) 0x97, (byte) 0x9F, 0, 46, (byte) 0x93, (byte) 0xA3, 0, 46, 9, (byte) 0xC3, 0, 46, (byte) 0xF5, (byte) 0xC5,
        0, 46, (byte) 0xDB, (byte) 0xC8, 0, 46, (byte) 0x9A, 61, 1, 46, (byte) 0xD9, (byte) 0x9D, 1, 46, (byte) 0xE0, (byte) 0xBA,
        1, 46, 57, 52, 2, 46, 4, (byte) 0xA7, 2, 46, 51, (byte) 0xAA, 2, 46, (byte) 0xEA, 24,
        3, 46, (byte) 0x9C, 72, 7, 46, (byte) 0xE1, 101, 7, 46, 52, 110, 7, 46, (byte) 0x91, 112,
        9, 46, (byte) 0xF6, 115, 9, 46, 92, 118, 14, 46, 102, (byte) 0x86, 14, 46, (byte) 0x99, (byte) 0x8A,
        14, 46, (byte) 0xC1, (byte) 0xB6, 14, 46, 84, (byte) 0xC9, 14, 46, 112, (byte) 0xCA, 14, 46, (byte) 0xEB, (byte) 0xDB,
        14, 46, (byte) 0xB0, (byte) 0xF5, 14, 46, 55, (byte) 0xF9, 14, 46, 20, (byte) 0xFB, 14, 46, 52, 14,
        15, 46, (byte) 0xFF, 54, 15, 46, 84, (byte) 0x8B, 15, 46, 58, (byte) 0xE8, 15, 46, (byte) 0xD3, 9,
        16, 46, 81, 52, 16, 46, (byte) 0xB7, (byte) 0xAA, 16, 46, 30, 85, 18, 46, (byte) 0xA9, (byte) 0xAF,
        19, 46, 123, (byte) 0xE8, 19, 46, 104, 16, 25, 46, 13, 20, 25, 46, 1, (byte) 0x87,
        39, 46, 99, (byte) 0x8C, 69, 46, (byte) 0xC0, (byte) 0x8C, 69, 46, (byte) 0xD9, (byte) 0x8C, 69, 46, 111, (byte) 0x8F,
        69, 46, 95, (byte) 0x90, 69, 46, (byte) 0xAA, (byte) 0x90, 69, 46, (byte) 0xDC, (byte) 0xDC, 69, 46
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(BASELINE);
    }
}
