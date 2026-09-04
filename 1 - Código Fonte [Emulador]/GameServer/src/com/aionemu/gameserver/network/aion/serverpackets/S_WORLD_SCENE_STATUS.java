package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_WORLD_SCENE_STATUS extends AionServerPacket {

	private int type;
	private int sceneId;
	private int unk;

	public S_WORLD_SCENE_STATUS(int type, int sceneId, int unk) {
		this.type = type;
		this.sceneId = sceneId;
		this.unk = unk;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(type);
		writeD(sceneId);
		writeD(unk);
	}
}
