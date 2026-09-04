package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * ascension quest's morph
 * 
 */
public class S_PLAY_MODE extends AionServerPacket {

	private int inascension;

	public S_PLAY_MODE(int inascension) {
		this.inascension = inascension;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(inascension);// if inascension =0x01 morph.
		writeC(0x00); // new 2.0 Packet --- probably pet info?
	}
}
