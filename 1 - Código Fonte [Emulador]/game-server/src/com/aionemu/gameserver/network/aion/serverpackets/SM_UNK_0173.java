package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0173 (371) - SM_UNK_0173 (4 bytes)
 * Official Classic 5.0 wire: writeD(val) sent in response to inventory slot changes (CM_MOVE_ITEM).
 */
public class SM_UNK_0173 extends AionServerPacket {
    private final int value;

    public SM_UNK_0173() {
        this(7);
    }

    public SM_UNK_0173(int value) {
        this.value = value;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(value);
    }
}
