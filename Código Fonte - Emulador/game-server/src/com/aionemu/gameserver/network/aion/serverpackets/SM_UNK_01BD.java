package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01BD (445) - SM_UNK_01BD (27 bytes)
 * Official Classic 5.0 achievement / progress step notification.
 */
public class SM_UNK_01BD extends AionServerPacket {
    private final int counter;

    public SM_UNK_01BD() {
        this(1);
    }

    public SM_UNK_01BD(int counter) {
        this.counter = counter;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
        writeD(11);
        writeC(2);
        writeD(0x17);
        writeD(0);
        writeD(counter);
        writeD(0);
        writeC(0);
    }
}
