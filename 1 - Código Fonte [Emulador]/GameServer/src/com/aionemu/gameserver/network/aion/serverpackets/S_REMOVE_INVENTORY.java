package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemDeleteType;

//Author Avol

public class S_REMOVE_INVENTORY extends AionServerPacket {

	private final int itemObjectId;
	private final ItemDeleteType deleteType;

	public S_REMOVE_INVENTORY(int itemObjectId) {
		this(itemObjectId, ItemDeleteType.QUEST_REWARD);
	}
	
	public S_REMOVE_INVENTORY(int itemObjectId, ItemDeleteType deleteType) {
		this.itemObjectId = itemObjectId;
		this.deleteType = deleteType;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(itemObjectId);
		writeD(deleteType.getMask());
	}
}
