package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01AB (427) - SM_UNK_01AB (3 bytes)
 * Official Classic 5.0: writeH(0) + writeC(2).
 */
public class SM_UNK_01AB extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
        writeC(2);
    }
}
