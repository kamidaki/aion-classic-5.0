package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class SM_USER_CLASSIC_WARDROBE_LOAD extends AionServerPacket {

	private final Player player;

	public SM_USER_CLASSIC_WARDROBE_LOAD(Player player) {
		this.player = player;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(1);
		writeD(this.player.getCommonData().getWardrobeSlot());
		writeC(this.player.getPlayerWardrobe().size());
		writeC(1);
		for (WardrobeEntry wardrobeEntry : this.player.getPlayerWardrobe().values()) {
			writeD(wardrobeEntry.getObjectId());
			writeD(wardrobeEntry.getItemId());
			writeD(wardrobeEntry.getColor());
			writeC(wardrobeEntry.isLiked() ? 1 : 0);
		}
	}
}
