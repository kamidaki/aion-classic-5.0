package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x015E (350) - SM_LEGION_TERRITORY_INFO (22 bytes)
 * Legion territory / domain state baseline.
 */
public class SM_LEGION_TERRITORY_INFO extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(1);
        writeH(1);
        writeH(1);
        writeB(new byte[14]);
    }
}
