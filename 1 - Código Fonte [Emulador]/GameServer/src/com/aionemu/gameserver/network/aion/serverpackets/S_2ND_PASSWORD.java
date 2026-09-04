package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_2ND_PASSWORD extends AionServerPacket {

	private int type; // 0: new passkey input window, 1: passkey input window, 2: message window
	private int messageType; // 0: newpasskey complete, 2: passkey edit complete, 3: passkey input
	private int wrongCount;
	private int unk;

	public S_2ND_PASSWORD(int type) {
		this.type = type;
	}

	public S_2ND_PASSWORD(int type, int messageType, int unk, int wrongCount) {
		this.type = type;
		this.messageType = messageType;
		this.unk = unk;
		this.wrongCount = wrongCount;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeC(type);

		switch (type) {
			case 0:
				break;
			case 1:
				break;
			case 2:
				writeH(messageType); // 0: newpasskey complete, 2: passkey edit complete, 3: passkey input
				writeB(new byte[5]); // 5.0 Classic padding (5 bytes de 0x00 conforme captura oficial)
				writeD(5); // server default value: 5 (max wrong count)
				break;
		}
	}
}
