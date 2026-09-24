package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0177 (375) - SM_UNK_0177 (6 bytes)
 * Official Classic 5.0 wire: writeH(0) + writeH(1) + writeH(0).
 */
public class SM_UNK_0177 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
        writeH(1);
        writeH(0);
    }
}
