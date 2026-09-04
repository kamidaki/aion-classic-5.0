package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_DP_USER extends AionServerPacket {

	private int playerObjectId;
	private int currentDp;

	public S_DP_USER(int playerObjectId, int currentDp) {
		this.playerObjectId = playerObjectId;
		this.currentDp = currentDp;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjectId);
		writeH(currentDp);
	}

}
