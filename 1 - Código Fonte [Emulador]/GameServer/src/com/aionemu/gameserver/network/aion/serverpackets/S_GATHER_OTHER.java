package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_GATHER_OTHER extends AionServerPacket {

	private int status;
	private int playerobjid;
	private int gatherableobjid;

	public S_GATHER_OTHER(int playerobjid, int gatherableobjid, int status) {
		this.playerobjid = playerobjid;
		this.gatherableobjid = gatherableobjid;
		this.status = status;
	}

	/**
	 * {@inheritDoc}
	 */

	@Override
	protected void writeImpl(AionConnection con) {

		writeD(playerobjid);
		writeD(gatherableobjid);
		writeH(0); // unk
		writeC(status);

	}
}
