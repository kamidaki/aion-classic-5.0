package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01AF (431) - SM_RADAR_INITIAL_STATE (5 bytes)
 * Area radar / minimap status baseline.
 */
public class SM_RADAR_INITIAL_STATE extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0);
        writeC(0);
    }
}
