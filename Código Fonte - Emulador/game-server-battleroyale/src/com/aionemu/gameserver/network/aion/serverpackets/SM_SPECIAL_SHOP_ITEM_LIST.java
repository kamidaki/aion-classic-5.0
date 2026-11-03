package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0113 (275) - SM_SPECIAL_SHOP_ITEM_LIST (756 bytes)
 * Official Classic 5.0: Special shop & event pass currency item list (58 baseline entries).
 */
public class SM_SPECIAL_SHOP_ITEM_LIST extends AionServerPacket {

    public static final byte[] BASELINE = new byte[] {
        58, 0, (byte) 0xF0, 2, 0, 0, (byte) 0xFF, (byte) 0xB0, (byte) 0xC8, 6, 0, 0, 0, 0, 3, (byte) 0xF1,
        2, 0, 0, 1, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xF2, 2, 0, 0,
        2, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xF3, 2, 0, 0, 3, (byte) 0xB1, (byte) 0xC8,
        6, 0, 0, 0, 0, 1, (byte) 0xF4, 2, 0, 0, 4, (byte) 0xB1, (byte) 0xC8, 6, 0, 0,
        0, 0, 1, (byte) 0xF5, 2, 0, 0, 5, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1,
        (byte) 0xF6, 2, 0, 0, 6, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xF7, 2, 0,
        0, 7, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xF8, 2, 0, 0, 8, (byte) 0xB1,
        (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xF9, 2, 0, 0, 9, (byte) 0xB1, (byte) 0xC8, 6, 0,
        0, 0, 0, 1, (byte) 0xFA, 2, 0, 0, 10, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0,
        1, (byte) 0xFB, 2, 0, 0, 11, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xFC, 2,
        0, 0, 12, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xFD, 2, 0, 0, 13,
        (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0xFE, 2, 0, 0, 14, (byte) 0xB1, (byte) 0xC8, 6,
        0, 0, 0, 0, 1, (byte) 0xFF, 2, 0, 0, 15, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0,
        0, 1, 0, 3, 0, 0, 16, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 1,
        3, 0, 0, 17, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 2, 3, 0, 0,
        18, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 3, 3, 0, 0, 19, (byte) 0xB1, (byte) 0xC8,
        6, 0, 0, 0, 0, 1, 4, 3, 0, 0, 20, (byte) 0xB1, (byte) 0xC8, 6, 0, 0,
        0, 0, 3, 5, 3, 0, 0, 21, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 3,
        6, 3, 0, 0, 22, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 7, 3, 0,
        0, 23, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 8, 3, 0, 0, 24, (byte) 0xB1,
        (byte) 0xC8, 6, 0, 0, 0, 0, 1, 9, 3, 0, 0, 25, (byte) 0xB1, (byte) 0xC8, 6, 0,
        0, 0, 0, 1, 10, 3, 0, 0, 26, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0,
        1, 11, 3, 0, 0, 27, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 12, 3,
        0, 0, 28, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 13, 3, 0, 0, 29,
        (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 105, 4, 0, 0, 30, (byte) 0xB1, (byte) 0xC8, 6,
        0, 0, 0, 0, 1, 106, 4, 0, 0, 31, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0,
        0, 1, 107, 4, 0, 0, 32, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 108,
        4, 0, 0, 33, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 109, 4, 0, 0,
        34, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 110, 4, 0, 0, 35, (byte) 0xB1, (byte) 0xC8,
        6, 0, 0, 0, 0, 1, 111, 4, 0, 0, 36, (byte) 0xB1, (byte) 0xC8, 6, 0, 0,
        0, 0, 1, 112, 4, 0, 0, 37, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1,
        122, 4, 0, 0, 38, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 123, 4, 0,
        0, 39, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, 124, 4, 0, 0, 40, (byte) 0xB1,
        (byte) 0xC8, 6, 0, 0, 0, 0, 1, 125, 4, 0, 0, 41, (byte) 0xB1, (byte) 0xC8, 6, 0,
        0, 0, 0, 1, 126, 4, 0, 0, 42, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0,
        1, 127, 4, 0, 0, 43, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x80, 4,
        0, 0, 44, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x81, 4, 0, 0, 45,
        (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x82, 4, 0, 0, 46, (byte) 0xB1, (byte) 0xC8, 6,
        0, 0, 0, 0, 1, (byte) 0x83, 4, 0, 0, 47, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0,
        0, 1, (byte) 0x84, 4, 0, 0, 48, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x85,
        4, 0, 0, 49, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x86, 4, 0, 0,
        50, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x87, 4, 0, 0, 51, (byte) 0xB1, (byte) 0xC8,
        6, 0, 0, 0, 0, 1, (byte) 0x88, 4, 0, 0, 52, (byte) 0xB1, (byte) 0xC8, 6, 0, 0,
        0, 0, 1, (byte) 0x89, 4, 0, 0, 53, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1,
        (byte) 0x8A, 4, 0, 0, 54, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x8B, 4, 0,
        0, 55, (byte) 0xB1, (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x8C, 4, 0, 0, 56, (byte) 0xB1,
        (byte) 0xC8, 6, 0, 0, 0, 0, 1, (byte) 0x8D, 4, 0, 0, 57, (byte) 0xB1, (byte) 0xC8, 6, 0,
        0, 0, 0, 1
    };

    private final byte[] payload;

    public SM_SPECIAL_SHOP_ITEM_LIST() {
        this.payload = BASELINE;
    }

    public SM_SPECIAL_SHOP_ITEM_LIST(byte[] payload) {
        this.payload = payload != null ? payload : BASELINE;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(payload);
    }
}
