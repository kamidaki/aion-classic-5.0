package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * dunno wtf this packet is doing. Not sure about id/name
 * 
 */
public class S_ENTER_WORLD_CHECK extends AionServerPacket {

	private byte msg = 0x01;
	private int characterId = 0;

	public S_ENTER_WORLD_CHECK(byte msg) {
		this.msg = msg;
	}

	public S_ENTER_WORLD_CHECK(int characterId) {
		this.msg = 0x01;
		this.characterId = characterId;
	}

	public S_ENTER_WORLD_CHECK() {
		this.msg = 0x01;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		int targetId = characterId != 0 ? characterId : (con.getActivePlayer() != null ? con.getActivePlayer().getObjectId() : 0);
		writeC(msg);
		writeC(0x00);
		writeC(0x00);
		writeC(0x00);
		writeD(0x00);
		writeD(targetId);
		writeD(0x17);
		writeD(0x00);
		writeD(0x00);
	}
}
