package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0105 (261) - SM_UNK_0105 (9 bytes)
 * Official Classic 5.0: writeD(val1) + writeD(val2) + writeC(flag).
 */
public class SM_UNK_0105 extends AionServerPacket {
    private final int val1;
    private final int val2;
    private final byte flag;

    public SM_UNK_0105() {
        this(0xC01AF6EA, 0, (byte) 0);
    }

    public SM_UNK_0105(int val1, int val2, byte flag) {
        this.val1 = val1;
        this.val2 = val2;
        this.flag = flag;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(val1);
        writeD(val2);
        writeC(flag);
    }
}
