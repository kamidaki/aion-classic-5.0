package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_STATUPDATE_DP extends AionServerPacket {

	private int currentDp;

	/**
	 * @param currentDp
	 */
	public SM_STATUPDATE_DP(int currentDp) {
		this.currentDp = currentDp;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(currentDp);
	}

}
