package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x014A (330) - SM_UNK_014A (0 bytes)
 * Official Classic 5.0 empty ping/sync packet.
 */
public class SM_UNK_014A extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
    }
}
