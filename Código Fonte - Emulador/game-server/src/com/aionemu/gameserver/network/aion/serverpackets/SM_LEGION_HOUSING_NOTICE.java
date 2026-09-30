package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x013A (314) - SM_LEGION_HOUSING_NOTICE (6 bytes)
 * Initial signaling for legion / housing module.
 */
public class SM_LEGION_HOUSING_NOTICE extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0);
        writeH(0);
    }
}
