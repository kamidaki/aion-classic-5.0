package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01AA (426) - SM_COSMETIC_TITLE_INIT (3 bytes)
 * Initialization of cosmetic titles and insignias.
 */
public class SM_COSMETIC_TITLE_INIT extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
        writeC(0);
    }
}
