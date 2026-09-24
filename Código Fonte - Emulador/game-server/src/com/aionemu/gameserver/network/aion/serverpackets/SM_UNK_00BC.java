package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x00BC (188) - SM_UNK_00BC (2 bytes)
 * Official Classic 5.0 wire: writeH(0).
 */
public class SM_UNK_00BC extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
    }
}
