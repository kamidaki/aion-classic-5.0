package com.aionemu.chatserver.network.aion.serverpackets;

import io.netty.buffer.ByteBuf;

import com.aionemu.chatserver.network.aion.AbstractServerPacket;
import com.aionemu.chatserver.network.netty.handler.ClientChannelHandler;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_PLAYER_AUTH_RESPONSE extends AbstractServerPacket {

	public SM_PLAYER_AUTH_RESPONSE() {
		super((byte) 0x02);
	}

	@Override
	protected void writeImpl(ClientChannelHandler clientChannelHandler, ByteBuf buf) {
		writeC(buf, getOpCode());
		writeC(buf, 0x40); // ?
		writeH(buf, 0x01); // ?
		writeD(buf, 0x00); // ?
		writeH(buf, 0x0822); // ?
	}
}
