package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_WIND_STATE_INFO extends AionServerPacket {
	private int bidirectional;
	private int mapId;
	private int streamId;
	private int state;
	
	public S_WIND_STATE_INFO(int bidirectional, int mapId, int streamId, int state) {
		this.bidirectional = bidirectional;
		this.mapId = mapId;
		this.streamId = streamId;
		this.state = state;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(bidirectional);
		writeD(mapId);
		writeD(streamId);
		writeC(state);
	}
}
