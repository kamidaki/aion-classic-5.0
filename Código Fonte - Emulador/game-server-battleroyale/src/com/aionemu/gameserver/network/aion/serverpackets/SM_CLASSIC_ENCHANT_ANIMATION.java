package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/** 0x01C3: 20 bytes measured in the official 5.0 enchanting capture. */
public class SM_CLASSIC_ENCHANT_ANIMATION extends AionServerPacket {
	private final int playerId, stoneId, templateId, duration, end;
	public SM_CLASSIC_ENCHANT_ANIMATION(Player player, Item stone, int duration, int end) {
		playerId = player.getObjectId(); stoneId = stone.getObjectId(); templateId = stone.getItemId();
		this.duration = duration; this.end = end;
	}
	@Override protected void writeImpl(AionConnection con) {
		writeD(playerId); writeD(stoneId); writeD(templateId); writeD(duration); writeD(end);
	}
}
