package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0182 (386) - SM_UNK_0182 (8 bytes)
 * Official Classic 5.0: writeD(val1) + writeD(val2).
 */
public class SM_UNK_0182 extends AionServerPacket {
    private final int val1;
    private final int val2;

    public SM_UNK_0182() {
        this(0x00036273, 0x802e4967);
    }

    public SM_UNK_0182(int val1, int val2) {
        this.val1 = val1;
        this.val2 = val2;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(val1);
        writeD(val2);
    }
}
