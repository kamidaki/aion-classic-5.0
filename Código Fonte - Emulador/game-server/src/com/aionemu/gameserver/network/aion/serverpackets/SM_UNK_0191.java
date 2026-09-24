package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0191 (401) - SM_UNK_0191 (8 bytes)
 * Official Classic 5.0 login sequence: writeD + writeD.
 */
public class SM_UNK_0191 extends AionServerPacket {
    private final int val1;
    private final int val2;

    public SM_UNK_0191() {
        this(0x4356b193, 0x000001a0);
    }

    public SM_UNK_0191(int val1, int val2) {
        this.val1 = val1;
        this.val2 = val2;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(val1);
        writeD(val2);
    }
}
