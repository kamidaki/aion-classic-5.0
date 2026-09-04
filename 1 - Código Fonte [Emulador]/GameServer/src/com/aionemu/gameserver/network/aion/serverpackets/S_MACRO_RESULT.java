package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_MACRO_RESULT extends AionServerPacket {

	public static S_MACRO_RESULT SM_MACRO_CREATED = new S_MACRO_RESULT(0x00);
	public static S_MACRO_RESULT SM_MACRO_DELETED = new S_MACRO_RESULT(0x01);

	private int code;

	private S_MACRO_RESULT(int code) {
		this.code = code;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(code);
	}
}
