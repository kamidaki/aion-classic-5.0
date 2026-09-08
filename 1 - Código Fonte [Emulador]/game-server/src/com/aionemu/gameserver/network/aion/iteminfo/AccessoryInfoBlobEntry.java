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
		writeQ(buf, (slots != null && slots.length > 0) ? slots[0].getSlotIdMask() : 0);
		// 5.0 Classic: a entrada de acessorio tem 16 bytes (u64 slot + 8 zeros).
		writeB(buf, new byte[8]);
	}

	@Override
	public int getSize() {
		return 16;
	}
}
