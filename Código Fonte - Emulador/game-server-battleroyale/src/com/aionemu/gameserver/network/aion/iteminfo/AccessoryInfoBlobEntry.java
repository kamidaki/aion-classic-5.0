package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

public class AccessoryInfoBlobEntry extends ItemBlobEntry {

	AccessoryInfoBlobEntry() {
		super(ItemBlobType.SLOTS_ACCESSORY);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemSlot[] slots = ItemSlot.getSlotsFor(item.getItemTemplate().getItemSlot());
		if (slots != null && slots.length > 1) {
			// Retail Classic 5.0: For 2-slot accessories (Rings, Earrings),
			// slot 1 is RIGHT (512 or 128) and slot 2 is LEFT (256 or 64).
			writeQ(buf, slots[1].getSlotIdMask());
			writeQ(buf, slots[0].getSlotIdMask());
		} else if (slots != null && slots.length == 1) {
			writeQ(buf, slots[0].getSlotIdMask());
			writeQ(buf, 0L);
		} else {
			writeQ(buf, 0L);
			writeQ(buf, 0L);
		}
	}

	@Override
	public int getSize() {
		return 16;
	}
}
