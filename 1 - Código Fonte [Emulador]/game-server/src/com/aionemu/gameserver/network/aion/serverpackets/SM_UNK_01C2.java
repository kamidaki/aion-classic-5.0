package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01C2 (450) - SM_UNK_01C2 (14 bytes)
 * Official Classic 5.0 wire: writeH(2) + writeH(5) + writeD(0) + writeH(6) + writeD(0).
 */
public class SM_UNK_01C2 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(2);
        writeH(5);
        writeD(0);
        writeH(6);
        writeD(0);
    }
}
