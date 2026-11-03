package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0181 (385) - SM_COMBAT_BURST_EFFECT (38 bytes)
 * Official Classic 5.0: Visual abnormal/burst effect application with 3D impact coordinates.
 * Counterpart of SM_COMBAT_BURST_REMOVE (0x0182).
 */
public class SM_COMBAT_BURST_EFFECT extends AionServerPacket {

    private final int count;
    private final int effectSkillId;
    private final int targetObjectId;
    private final int remainingTimeMs;
    private final int totalDurationMs;
    private final long startTimeUnix;
    private final float x;
    private final float y;
    private final float z;
    private final byte[] customPayload;

    private static final byte[] BASELINE = new byte[] {
        1, 0, 77, 108, 3, 0, 81, (byte) 0xD0, 33, (byte) 0x80, (byte) 0xA0, (byte) 0x86, 1, 0, (byte) 0xA0, (byte) 0x86,
        1, 0, (byte) 0x8A, (byte) 0xFD, (byte) 0x90, 106, 0, 0, 0, 0, (byte) 0xDE, 73, 24, 68, (byte) 0x8A, (byte) 0xD2,
        48, 68, (byte) 0xE1, (byte) 0x8D, (byte) 0xB1, 67
    };

    /**
     * Default canonical baseline constructor (from official Wireshark capture).
     */
    public SM_COMBAT_BURST_EFFECT() {
        this.count = 1;
        this.effectSkillId = 0x00036C4D;
        this.targetObjectId = 0x8021D051;
        this.remainingTimeMs = 100000;
        this.totalDurationMs = 100000;
        this.startTimeUnix = 0x6A90FD8AL;
        this.x = 609.1542f;
        this.y = 707.2897f;
        this.z = 355.1084f;
        this.customPayload = null;
    }

    /**
     * Dynamic effect constructor with target and 3D world coordinates.
     */
    public SM_COMBAT_BURST_EFFECT(int effectSkillId, int targetObjectId, int remainingTimeMs, int totalDurationMs,
                                  long startTimeUnix, float x, float y, float z) {
        this.count = 1;
        this.effectSkillId = effectSkillId;
        this.targetObjectId = targetObjectId;
        this.remainingTimeMs = remainingTimeMs;
        this.totalDurationMs = totalDurationMs;
        this.startTimeUnix = startTimeUnix;
        this.x = x;
        this.y = y;
        this.z = z;
        this.customPayload = null;
    }

    public SM_COMBAT_BURST_EFFECT(byte[] rawPayload) {
        this.count = 1;
        this.effectSkillId = 0;
        this.targetObjectId = 0;
        this.remainingTimeMs = 0;
        this.totalDurationMs = 0;
        this.startTimeUnix = 0;
        this.x = 0;
        this.y = 0;
        this.z = 0;
        this.customPayload = rawPayload;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        if (customPayload != null) {
            writeB(customPayload);
            return;
        }
        writeH(count);
        writeD(effectSkillId);
        writeD(targetObjectId);
        writeD(remainingTimeMs);
        writeD(totalDurationMs);
        writeQ(startTimeUnix);
        writeF(x);
        writeF(y);
        writeF(z);
    }
}
