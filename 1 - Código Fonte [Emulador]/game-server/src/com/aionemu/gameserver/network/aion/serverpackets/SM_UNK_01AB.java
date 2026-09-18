package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01AB (427) - SM_UNK_01AB (3 bytes)
 * Official Classic 5.0: writeH(0) + writeC(2).
 */
public class SM_UNK_01AB extends AionServerPacket {
    private final java.util.Map<Integer, Integer> points;
    public SM_UNK_01AB() { this(java.util.Map.of()); }
    public SM_UNK_01AB(java.util.Map<Integer, Integer> points) { this.points = java.util.Map.copyOf(points); }
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(points.size());
        for (var entry : points.entrySet()) { writeD(entry.getKey()); writeH(entry.getValue()); }
        writeC(2);
    }
}
