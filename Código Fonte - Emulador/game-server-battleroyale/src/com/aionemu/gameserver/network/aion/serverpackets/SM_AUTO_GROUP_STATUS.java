package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0135 (309) - SM_AUTO_GROUP_STATUS (19 bytes)
 * Official Classic 5.0: Automatic group / instance matchmaking registration status.
 * Payload pattern: writeD(instanceId) + writeC(status) + writeC(subStatus) + writeD(minLevel) + writeD(maxLevel) + writeD(0) + writeC(0)
 */
public class SM_AUTO_GROUP_STATUS extends AionServerPacket {

    private final int instanceMaskId;
    private final int status;
    private final int subStatus;
    private final int minLevel;
    private final int maxLevel;
    private final int extra;
    private final int flag;

    /**
     * Default canonical baseline constructor (Chantra Dredgion / Arena 0x67).
     */
    public SM_AUTO_GROUP_STATUS() {
        this(0x67, 1, 2, 0x4B, 0x4B, 0, 0);
    }

    public SM_AUTO_GROUP_STATUS(int instanceMaskId, int status, int subStatus, int minLevel, int maxLevel) {
        this(instanceMaskId, status, subStatus, minLevel, maxLevel, 0, 0);
    }

    public SM_AUTO_GROUP_STATUS(int instanceMaskId, int status, int subStatus, int minLevel, int maxLevel, int extra, int flag) {
        this.instanceMaskId = instanceMaskId;
        this.status = status;
        this.subStatus = subStatus;
        this.minLevel = minLevel;
        this.maxLevel = maxLevel;
        this.extra = extra;
        this.flag = flag;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(instanceMaskId);
        writeC(status);
        writeC(subStatus);
        writeD(minLevel);
        writeD(maxLevel);
        writeD(extra);
        writeC(flag);
    }
}
