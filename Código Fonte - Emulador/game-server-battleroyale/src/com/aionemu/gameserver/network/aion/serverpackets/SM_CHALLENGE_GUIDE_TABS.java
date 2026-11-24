package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01C2 (450) - SM_CHALLENGE_GUIDE_TABS (14 bytes)
 * Challenge task and pass guide tab baseline registration.
 */
public class SM_CHALLENGE_GUIDE_TABS extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(2);
        writeH(5);
        writeD(0);
        writeH(6);
        writeD(0);
    }
}
