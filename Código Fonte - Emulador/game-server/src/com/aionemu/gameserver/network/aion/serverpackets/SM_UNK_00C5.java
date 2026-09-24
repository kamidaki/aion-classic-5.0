package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x00C5 (197) - SM_UNK_00C5 (13 bytes)
 * Official Classic 5.0: writeD(target) + writeC(action) + writeD(val1) + writeD(val2).
 */
public class SM_UNK_00C5 extends AionServerPacket {
    private final int targetId;
    private final byte action;
    private final int val1;
    private final int val2;

    public SM_UNK_00C5() {
        this(0x8003236F, (byte) 3, 13, 0);
    }

    public SM_UNK_00C5(int targetId, byte action, int val1, int val2) {
        this.targetId = targetId;
        this.action = action;
        this.val1 = val1;
        this.val2 = val2;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(targetId);
        writeC(action);
        writeD(val1);
        writeD(val2);
    }
}
