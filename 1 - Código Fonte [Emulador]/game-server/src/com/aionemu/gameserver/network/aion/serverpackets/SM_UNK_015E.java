package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x015E (350) - SM_UNK_015E (22 bytes)
 * Official Classic 5.0 wire: writeD(1) + writeH(1) + writeH(1) + 14 zero bytes.
 */
public class SM_UNK_015E extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(1);
        writeH(1);
        writeH(1);
        writeB(new byte[14]);
    }
}
