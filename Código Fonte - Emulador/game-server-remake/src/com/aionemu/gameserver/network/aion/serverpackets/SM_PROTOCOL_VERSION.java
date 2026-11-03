package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x017F (383) - SM_PROTOCOL_VERSION (10 bytes)
 * Official Classic 5.0 handshake: writeD(token) + writeS(version).
 */
public class SM_PROTOCOL_VERSION extends AionServerPacket {
    private final int token;
    private final String version;

    public SM_PROTOCOL_VERSION() {
        this(0x7638fcf1, "3/0/0");
    }

    public SM_PROTOCOL_VERSION(int token, String version) {
        this.token = token;
        this.version = version;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(token);
        writeS(version);
    }
}
