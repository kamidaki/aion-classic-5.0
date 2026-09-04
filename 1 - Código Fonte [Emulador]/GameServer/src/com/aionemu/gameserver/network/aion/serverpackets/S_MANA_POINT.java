package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * This packet is used to update mp / max mp value.
 * 
 */
public class S_MANA_POINT extends AionServerPacket {

	private int currentMp;
	private int maxMp;

	/**
	 * @param currentMp
	 * @param maxMp
	 */
	public S_MANA_POINT(int currentMp, int maxMp) {
		this.currentMp = currentMp;
		this.maxMp = maxMp;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(currentMp);
		writeD(maxMp);
	}

}
