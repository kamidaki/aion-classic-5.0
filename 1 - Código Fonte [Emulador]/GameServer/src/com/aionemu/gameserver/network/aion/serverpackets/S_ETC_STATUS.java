package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


//TODO Rename
public class S_ETC_STATUS extends AionServerPacket {

	private Player player;
	private int action;

	public S_ETC_STATUS(int action, Player player) {
		this.action = action;
		this.player = player;
	}


	@Override
	protected void writeImpl(AionConnection con) {
		writeC(action);
		writeD(player.getObjectId());
		switch(action){
			case 0:
				writeD(player.getAbyssRank().getRank().getId());
				break;
			case 1:
			case 2:
				if (player.isMentor())
					writeD(1);
				else
					writeD(0);
				break;
		}
	}
}
