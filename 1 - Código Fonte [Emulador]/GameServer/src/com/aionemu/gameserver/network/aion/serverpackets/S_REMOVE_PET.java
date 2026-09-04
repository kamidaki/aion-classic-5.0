package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_REMOVE_PET extends AionServerPacket {

	private int summonObjId;

	public S_REMOVE_PET(int summonObjId) {
		this.summonObjId = summonObjId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(summonObjId);
	}
}
