package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0148 (328) - SM_UNK_0148 (36 bytes)
 * Official Classic 5.0: writeD(0x1274) + 32 zero bytes.
 */
public class SM_UNK_0148 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0x1274);
        writeB(new byte[32]);
    }
}
