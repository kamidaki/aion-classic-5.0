package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0092 (146) - SM_ENTER_WORLD_NOTIFY (12 bytes)
 * Official Classic 5.0 enter world notification: writeD + writeD + writeD.
 */
public class SM_ENTER_WORLD_NOTIFY extends AionServerPacket {
    private final int val1;
    private final int val2;
    private final int status;

    public SM_ENTER_WORLD_NOTIFY() {
        this(0x173eed80, 0x80da3aa6, 1);
    }

    public SM_ENTER_WORLD_NOTIFY(int val1, int val2, int status) {
        this.val1 = val1;
        this.val2 = val2;
        this.status = status;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(val1);
        writeD(val2);
        writeD(status);
    }
}
