package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0191 (401) - SM_RENDER_GRAPHIC_INIT (8 bytes)
 * Render engine / graphic subsystem handshake.
 */
public class SM_RENDER_GRAPHIC_INIT extends AionServerPacket {
    private final int val1;
    private final int val2;

    public SM_RENDER_GRAPHIC_INIT() {
        this(0x46524830, 416);
    }

    public SM_RENDER_GRAPHIC_INIT(int val1, int val2) {
        this.val1 = val1;
        this.val2 = val2;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(val1);
        writeD(val2);
    }
}
