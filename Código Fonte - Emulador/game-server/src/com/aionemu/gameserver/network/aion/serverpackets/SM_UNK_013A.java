package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x013A (314) - SM_UNK_013A (6 bytes)
 * Official Classic 5.0 wire: writeD(0) + writeH(0).
 */
public class SM_UNK_013A extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0);
        writeH(0);
    }
}
