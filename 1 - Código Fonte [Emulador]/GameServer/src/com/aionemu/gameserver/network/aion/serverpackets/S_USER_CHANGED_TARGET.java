package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_USER_CHANGED_TARGET extends AionServerPacket {

	private Player player;

	public S_USER_CHANGED_TARGET(Player player) {
		this.player = player;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(player.getObjectId());
		writeD(player.getTarget() == null ? 0 : player.getTarget().getObjectId());
	}
}
