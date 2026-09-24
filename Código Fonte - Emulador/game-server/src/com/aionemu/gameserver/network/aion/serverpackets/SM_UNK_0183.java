package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0183 (387) - SM_UNK_0183 (2 bytes)
 * Official Classic 5.0: writeH(1).
 */
public class SM_UNK_0183 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
    }
}
