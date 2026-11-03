package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0110 (272) - SM_ACHIEVEMENT_SEASON_EVENT_INFO (36 bytes)
 * Official Classic 5.0: Active achievement season & battlepass event synchronization.
 */
public class SM_ACHIEVEMENT_SEASON_EVENT_INFO extends AionServerPacket {

    private final int count;
    private final long seasonEventObjectId;
    private final int step;
    private final int isCurrentSeason;
    private final byte[] tail;

    private static final byte[] BASELINE = new byte[] {
        1, 0, 88, 109, 32, 15, 0, 0, 0, 0, 2, 1, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 1
    };

    public SM_ACHIEVEMENT_SEASON_EVENT_INFO() {
        this.count = 1;
        this.seasonEventObjectId = 0x0F206D58L;
        this.step = 2;
        this.isCurrentSeason = 1;
        this.tail = new byte[24];
        this.tail[23] = 1;
    }

    public SM_ACHIEVEMENT_SEASON_EVENT_INFO(long seasonEventObjectId, int step, int isCurrentSeason) {
        this.count = 1;
        this.seasonEventObjectId = seasonEventObjectId;
        this.step = step;
        this.isCurrentSeason = isCurrentSeason;
        this.tail = new byte[24];
        this.tail[23] = 1;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(count);
        writeQ(seasonEventObjectId);
        writeC(step);
        writeC(isCurrentSeason);
        writeB(tail);
    }
}
