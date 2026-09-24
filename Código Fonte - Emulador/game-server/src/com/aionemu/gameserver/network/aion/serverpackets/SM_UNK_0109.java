package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0109 (265) - SM_UNK_0109 (3 bytes)
 * Official Classic 5.0: writeH(1) + writeC(0).
 */
public class SM_UNK_0109 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
        writeC(0);
    }
}
