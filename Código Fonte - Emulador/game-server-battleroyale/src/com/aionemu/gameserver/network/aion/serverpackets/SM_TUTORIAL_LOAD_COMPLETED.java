package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01C0 (448) - SM_TUTORIAL_LOAD_COMPLETED (2 bytes)
 * Signal for tutorial assets loading completion.
 */
public class SM_TUTORIAL_LOAD_COMPLETED extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
    }
}
