package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x014A (330) - SM_NETWORK_SYNC_ACK (0 bytes)
 * Official Classic 5.0 empty network ping / sync ack packet.
 */
public class SM_NETWORK_SYNC_ACK extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
    }
}
