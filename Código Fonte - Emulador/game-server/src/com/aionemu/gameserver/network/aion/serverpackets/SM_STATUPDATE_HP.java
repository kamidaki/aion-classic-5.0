package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_STATUPDATE_HP extends AionServerPacket {

	private int currentHp;
	private int maxHp;

	/**
	 * @param currentHp
	 * @param maxHp
	 */
	public SM_STATUPDATE_HP(int currentHp, int maxHp) {
		this.currentHp = currentHp;
		this.maxHp = maxHp;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(currentHp);
		writeD(maxHp);
	}

}
