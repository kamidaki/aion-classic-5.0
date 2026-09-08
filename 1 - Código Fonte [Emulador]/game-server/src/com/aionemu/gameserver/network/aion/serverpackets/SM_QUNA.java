package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class SM_QUNA extends AionServerPacket {

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(254);
        writeB(new byte[] { 0x2A, 0x01 });
        writeQ(500);
    }
}
