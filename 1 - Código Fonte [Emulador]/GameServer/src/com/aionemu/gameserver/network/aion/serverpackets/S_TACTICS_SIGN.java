package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_TACTICS_SIGN extends AionServerPacket {

	private int brandId;
	private int targetObjectId;

	public S_TACTICS_SIGN(int brandId, int targetObjectId) {
		this.brandId = brandId;
		this.targetObjectId = targetObjectId;
	}

	@Override
	protected void writeImpl(AionConnection con) {

		writeH(0x01);
		writeD(0x01); // unk
		writeD(brandId);
		writeD(targetObjectId);

	}
}
