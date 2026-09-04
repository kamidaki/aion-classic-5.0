package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_CHANGE_GUILD_MEMBER_INTRO extends AionServerPacket {

	private String selfintro;
	private int playerObjId;

	public S_CHANGE_GUILD_MEMBER_INTRO(int playerObjId, String selfintro) {
		this.selfintro = selfintro;
		this.playerObjId = playerObjId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjId);
		writeS(selfintro);
	}
}
