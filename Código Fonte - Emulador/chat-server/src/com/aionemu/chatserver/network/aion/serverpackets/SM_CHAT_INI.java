package com.aionemu.chatserver.network.aion.serverpackets;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.network.aion.AbstractServerPacket;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_CHAT_INI extends AbstractServerPacket {

	public SM_CHAT_INI() {
		super((byte) 0x31);
	}

	@Override
	protected void writeImpl(ClientChannelHandler cHandler, ByteBuf buf) {
		writeC(buf, getOpCode());
		writeC(buf, 0x40);
		writeD(buf, 0x02);
		writeH(buf, 0x00);
	}
}
