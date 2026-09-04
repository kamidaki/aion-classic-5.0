package com.aionemu.gameserver.network.chatserver;

import com.aionemu.commons.network.packet.BaseServerPacket;

import java.nio.Buffer;
import java.nio.ByteBuffer;

public abstract class CsServerPacket extends BaseServerPacket
{
    protected CsServerPacket(int opcode) {
        super(opcode);
    }
	
    public final void write(ChatServerConnection con, ByteBuffer buffer) {
        setBuf(buffer);
        buf.putShort((short) 0);
        buf.put((byte) getOpcode());
        writeImpl(con);
        ((Buffer) buf).flip();
        buf.putShort((short) buf.limit());
        ((Buffer) buf).position(0);
    }
	
    protected abstract void writeImpl(ChatServerConnection con);
}