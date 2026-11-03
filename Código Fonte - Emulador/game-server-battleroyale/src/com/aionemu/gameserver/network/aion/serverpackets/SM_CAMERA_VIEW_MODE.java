package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0183 (387) - SM_CAMERA_VIEW_MODE (2 bytes)
 * Flag for map camera / panoramic overview mode.
 */
public class SM_CAMERA_VIEW_MODE extends AionServerPacket {
    @Override
    protected void writeImpl(AionConnection con) {
        writeH(1);
    }
}
