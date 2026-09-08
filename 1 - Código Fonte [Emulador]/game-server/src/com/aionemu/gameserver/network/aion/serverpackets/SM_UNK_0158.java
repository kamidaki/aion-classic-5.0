package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0158 (344) - SM_UNK_0158 (8 bytes)
 * Official Classic 5.0 wire: writeQ(0).
 */
public class SM_UNK_0158 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeQ(0);
    }
}
