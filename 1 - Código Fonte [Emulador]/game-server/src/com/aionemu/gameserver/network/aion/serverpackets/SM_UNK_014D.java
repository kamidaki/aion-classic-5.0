package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x014D (333) - SM_UNK_014D (6 bytes)
 * Official Classic 5.0: writeD(objectId) + writeH(0).
 */
public class SM_UNK_014D extends AionServerPacket {
    private final int objectId;

    public SM_UNK_014D(int objectId) {
        this.objectId = objectId;
    }

    public SM_UNK_014D() {
        this(0);
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(objectId);
        writeH(0);
    }
}
