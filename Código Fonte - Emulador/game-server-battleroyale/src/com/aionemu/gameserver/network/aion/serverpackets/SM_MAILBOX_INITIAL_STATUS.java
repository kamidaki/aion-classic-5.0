package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01B3 (435) - SM_MAILBOX_INITIAL_STATUS (2 bytes)
 * Initial mailbox status indicator.
 */
public class SM_MAILBOX_INITIAL_STATUS extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
    }
}
