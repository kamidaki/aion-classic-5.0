package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0170 (368) - SM_ZONE_HAZARD_LIST (2 bytes)
 * Official Classic 5.0 wire: writeH(hazardZonesCount).
 * Transmits count of active dynamic hazard / weather sectors for the current world map.
 */
public class SM_ZONE_HAZARD_LIST extends AionServerPacket {

    private final int hazardCount;

    public SM_ZONE_HAZARD_LIST() {
        this(0);
    }

    public SM_ZONE_HAZARD_LIST(int hazardCount) {
        this.hazardCount = hazardCount;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(hazardCount);
    }
}
