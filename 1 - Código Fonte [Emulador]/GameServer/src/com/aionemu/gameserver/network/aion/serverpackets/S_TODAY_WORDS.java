package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.utils.PacketSendUtility;


public class S_TODAY_WORDS extends AionServerPacket {

	private int targetObjId;
	private String note;

	public S_TODAY_WORDS(int targetObjId, String note) {
		this.targetObjId = targetObjId;
		this.note = note;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(targetObjId);
		writeS(note);
		PacketSendUtility.sendPacket(con.getActivePlayer(), new S_MESSAGE_CODE(1390124, note));
		System.out.print("work");
	}
}
