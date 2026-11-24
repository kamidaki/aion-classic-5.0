package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0127 (295) - SM_CUBE_TAB_EXPANSION_INFO (20 bytes)
 * Cube / bag expansion tabs initialization.
 */
public class SM_CUBE_TAB_EXPANSION_INFO extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(9);
        for (int i = 0; i < 9; i++) {
            writeH(i);
        }
    }
}
