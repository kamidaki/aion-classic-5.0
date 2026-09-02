package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Rinzler (Encom)
 */
public class S_WORLD extends AionServerPacket
{
	private final Player player;
	
	public S_WORLD(Player player) {
		super();
		this.player = player;
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(player.getWorldId());
		writeD(player.getWorldId());
		writeB(new byte[5]);
		writeF(player.getX());
		writeF(player.getY());
		writeF(player.getZ());
		writeC(player.getHeading());
		writeC(0x14);
		writeB(new byte[15]);
	}
}