package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0146 (326) - SM_UNK_0146 (8 bytes)
 * Official Classic 5.0: writeD(objectId) + writeD(0).
 */
public class SM_UNK_0146 extends AionServerPacket {
    private final int objectId;

    public SM_UNK_0146(int objectId) {
        this.objectId = objectId;
    }

    public SM_UNK_0146() {
        this(0);
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(objectId);
        writeD(0);
    }
}
