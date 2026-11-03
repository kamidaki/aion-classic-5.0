package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Server packet for Daeva Pass / Season data (Opcode 0x019F in 5.0 Classic).
 */
public class S_DAEVA_PASS_DATA extends AionServerPacket {

	private byte[] payload;

	public S_DAEVA_PASS_DATA() {
		this(null);
	}

	public S_DAEVA_PASS_DATA(byte[] payload) {
		this.payload = payload;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (payload != null) {
			writeB(payload);
		} else {
			writeC(1);
			writeH(26);
			writeD(1000);
			writeD(1);
			writeD(-1);
			writeD(3900);
			writeS("Onnix");
			writeB(new byte[750]);
		}
	}
}
