package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0197 (407) - SM_UNK_0197 (6 bytes)
 * Official Classic 5.0 warmup: writeD(objectId) + writeH(0).
 */
public class SM_UNK_0197 extends AionServerPacket {
    private final int objectId;

    public SM_UNK_0197(int objectId) {
        this.objectId = objectId;
    }

    public SM_UNK_0197() {
        this(0);
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(objectId);
        writeH(0);
    }
}
