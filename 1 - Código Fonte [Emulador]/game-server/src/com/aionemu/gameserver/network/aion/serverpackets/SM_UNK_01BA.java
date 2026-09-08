package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01BA (442) - SM_UNK_01BA (3 bytes)
 * Official Classic 5.0 wire: writeH(1) + writeC(0).
 */
public class SM_UNK_01BA extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
        writeC(0);
    }
}
