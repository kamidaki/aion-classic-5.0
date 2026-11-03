package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x018C (396) - SM_TERRAIN_SECTOR_INFO (216 bytes)
 * Active terrain mesh and physical sector parameters.
 */
public class SM_TERRAIN_SECTOR_INFO extends AionServerPacket {
    private static final byte[] BASELINE = new byte[] {
        (byte) 0xD4, 0, 0, 0, 20, 0, 0, 0, 0, 0, 14, 0, 24, 0, 4, 0,
        8, 0, 12, 0, 16, 0, 20, 0, 14, 0, 0, 0, (byte) 0x87, 83, 113, 20,
        124, (byte) 0xEE, (byte) 0xEB, 115, (byte) 0x90, 0, 0, 0, 120, 0, 0, 0, 4, 0, 0, 0,
        (byte) 0x80, 0, 0, 0, 62, 38, 48, 108, 17, 37, 103, (byte) 0x91, (byte) 0xC0, (byte) 0xE0, (byte) 0x9E, (byte) 0xDA,
        121, 19, 117, (byte) 0xDA, (byte) 0xC6, (byte) 0xAD, 76, 77, 98, 115, (byte) 0xEE, (byte) 0xEE, (byte) 0xE6, (byte) 0x9A, 27, (byte) 0x99,
        85, (byte) 0xE8, (byte) 0xA3, (byte) 0x8F, 42, (byte) 0xF1, 75, 59, 101, 113, (byte) 0xEB, 44, 32, 119, (byte) 0x8F, 102,
        (byte) 0xE0, 44, 36, (byte) 0x85, (byte) 0x80, 106, 113, (byte) 0x95, 84, 61, 10, 52, 119, 119, (byte) 0xA6, 23,
        90, 33, 37, (byte) 0x9A, (byte) 0xEE, (byte) 0xE6, 126, (byte) 0xCE, 17, (byte) 0x9E, (byte) 0xDB, (byte) 0x8C, 59, 64, 22, (byte) 0x8D,
        (byte) 0xA2, 92, (byte) 0xD8, 43, 82, (byte) 0xFC, (byte) 0xAF, (byte) 0x9B, (byte) 0x83, 58, 110, (byte) 0xB1, 52, (byte) 0xD9, (byte) 0x97, (byte) 0xC8,
        (byte) 0xCC, 46, (byte) 0xFD, (byte) 0xD6, 53, (byte) 0x9E, (byte) 0x95, 29, (byte) 0x9E, 103, (byte) 0xDE, (byte) 0xC9, 120, (byte) 0xB3, (byte) 0xE8, 62,
        54, (byte) 0xC7, 68, 70, (byte) 0xD2, 95, (byte) 0x83, (byte) 0x80, (byte) 0xA4, (byte) 0xC2, (byte) 0xA8, 65, (byte) 0x8A, 91, 42, 64,
        (byte) 0xB7, 24, 80, (byte) 0xC7, 32, 0, 0, 0, (byte) 0xCA, (byte) 0xEE, (byte) 0x9A, (byte) 0xC8, (byte) 0xAD, 49, 100, 72,
        9, (byte) 0x9F, (byte) 0xA2, 115, (byte) 0xE7, 60, 28, (byte) 0x98, 62, 41, (byte) 0xFF, 2, 119, 44, 50, (byte) 0xAF,
        67, 39, (byte) 0xD2, (byte) 0x9C, (byte) 0x94, 85, 21, (byte) 0xA7
    };

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(BASELINE);
    }
}
