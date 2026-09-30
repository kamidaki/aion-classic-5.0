package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0177 (375) - SM_EQUIPMENT_VIEW_STATE (6 bytes)
 * Official Classic 5.0 wire: writeH(0) + writeH(1) + writeH(0).
 * Controls equipment/wardrobe display state on client enter world.
 */
public class SM_EQUIPMENT_VIEW_STATE extends AionServerPacket {

    private final int viewType;
    private final int count;
    private final int state;

    public SM_EQUIPMENT_VIEW_STATE() {
        this(0, 1, 0);
    }

    public SM_EQUIPMENT_VIEW_STATE(int viewType, int count, int state) {
        this.viewType = viewType;
        this.count = count;
        this.state = state;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(viewType);
        writeH(count);
        writeH(state);
    }
}
