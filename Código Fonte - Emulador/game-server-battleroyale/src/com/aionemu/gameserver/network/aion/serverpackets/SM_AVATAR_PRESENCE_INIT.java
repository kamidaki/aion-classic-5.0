package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0197 (407) - SM_AVATAR_PRESENCE_INIT (6 bytes)
 * Local avatar presence confirmation.
 */
public class SM_AVATAR_PRESENCE_INIT extends AionServerPacket {
    private final int objectId;

    public SM_AVATAR_PRESENCE_INIT(int objectId) {
        this.objectId = objectId;
    }

    public SM_AVATAR_PRESENCE_INIT() {
        this(0);
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(objectId);
        writeH(0);
    }
}
