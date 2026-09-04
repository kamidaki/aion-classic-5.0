package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * This packet is used to update current hp and max hp values.
 * 
 */
public class S_HIT_POINT extends AionServerPacket {

	private int currentHp;
	private int maxHp;

	/**
	 * @param currentHp
	 * @param maxHp
	 */
	public S_HIT_POINT(int currentHp, int maxHp) {
		this.currentHp = currentHp;
		this.maxHp = maxHp;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(currentHp);
		writeD(maxHp);
	}

}
