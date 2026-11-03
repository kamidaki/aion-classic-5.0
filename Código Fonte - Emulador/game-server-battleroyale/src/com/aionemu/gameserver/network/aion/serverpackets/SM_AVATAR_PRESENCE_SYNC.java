package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01A8 (424) - SM_AVATAR_PRESENCE_SYNC (6 bytes)
 * Secondary avatar presence sync.
 */
public class SM_AVATAR_PRESENCE_SYNC extends AionServerPacket {
    private final int objectId;

    public SM_AVATAR_PRESENCE_SYNC(int objectId) {
        this.objectId = objectId;
    }

    public SM_AVATAR_PRESENCE_SYNC() {
        this(0);
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(objectId);
        writeH(0);
    }
}
