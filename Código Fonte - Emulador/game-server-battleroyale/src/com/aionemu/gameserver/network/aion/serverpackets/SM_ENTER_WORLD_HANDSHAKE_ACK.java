package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01C5 (453) - SM_ENTER_WORLD_HANDSHAKE_ACK (3 bytes)
 * Final handshake ACK confirming world entrance completion.
 */
public class SM_ENTER_WORLD_HANDSHAKE_ACK extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(0);
        writeC(2);
    }
}
