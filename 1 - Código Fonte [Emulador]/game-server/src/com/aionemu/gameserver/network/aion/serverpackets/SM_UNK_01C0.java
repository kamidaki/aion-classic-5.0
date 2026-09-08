package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01C0 (448) - SM_UNK_01C0 (2 bytes)
 * Official Classic 5.0 wire: writeH(0).
 */
public class SM_UNK_01C0 extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
    }
}
