package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

public class WingInfoBlobEntry extends ItemBlobEntry {

	WingInfoBlobEntry() {
		super(ItemBlobType.SLOTS_WING);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemSlot[] slots = ItemSlot.getSlotsFor(item.getItemTemplate().getItemSlot());
		writeQ(buf, (slots != null && slots.length > 0) ? slots[0].getSlotIdMask() : ItemSlot.WINGS.getSlotIdMask());
	}

	@Override
	public int getSize() {
		return 8;
	}
}
