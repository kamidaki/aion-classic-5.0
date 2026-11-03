package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0109 (265) - SM_TUTORIAL_GUIDE_STATE (3 bytes)
 * Official Classic 5.0: writeH(guideId) + writeC(state).
 * Controls quick guide / tutorial completion indicator in UI.
 */
public class SM_TUTORIAL_GUIDE_STATE extends AionServerPacket {

    private final int guideId;
    private final int state;

    public SM_TUTORIAL_GUIDE_STATE() {
        this(1, 0);
    }

    public SM_TUTORIAL_GUIDE_STATE(int guideId, int state) {
        this.guideId = guideId;
        this.state = state;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(guideId);
        writeC(state);
    }
}
