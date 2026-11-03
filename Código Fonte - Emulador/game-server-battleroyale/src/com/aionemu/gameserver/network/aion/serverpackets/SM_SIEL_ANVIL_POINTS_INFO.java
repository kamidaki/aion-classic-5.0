package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import java.util.Map;

/**
 * Opcode 0x01AB (427) - SM_SIEL_ANVIL_POINTS_INFO (3+ bytes)
 * Siel Anvil points synchronization.
 */
public class SM_SIEL_ANVIL_POINTS_INFO extends AionServerPacket {
    private final Map<Integer, Integer> points;

    public SM_SIEL_ANVIL_POINTS_INFO() {
        this(Map.of());
    }

    public SM_SIEL_ANVIL_POINTS_INFO(Map<Integer, Integer> points) {
        this.points = Map.copyOf(points);
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(points.size());
        for (var entry : points.entrySet()) {
            writeD(entry.getKey());
            writeH(entry.getValue());
        }
        writeC(2);
    }
}
