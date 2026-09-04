package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * This packet is response for CM_QUIT
 * 
 */
public class S_ASK_QUIT_RESULT extends AionServerPacket {

	private boolean edit_mode = false;

	public S_ASK_QUIT_RESULT() {
	}

	public S_ASK_QUIT_RESULT(boolean edit_mode) {
		this.edit_mode = edit_mode;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(edit_mode ? 2 : 1);// 1 normal, 2 plastic surgery/gender switch
		writeC(0x00);// unk
		writeC(0xFF);//why sometime 0x2e?
		writeC(0xFF);
		writeC(0xFF);
		writeC(0xFF);
	}
}
