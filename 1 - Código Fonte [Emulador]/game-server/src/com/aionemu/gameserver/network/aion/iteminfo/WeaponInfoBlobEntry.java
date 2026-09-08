package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

public class WeaponInfoBlobEntry extends ItemBlobEntry {

	WeaponInfoBlobEntry() {
		super(ItemBlobType.SLOTS_WEAPON);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemSlot[] slots = ItemSlot.getSlotsFor(item.getItemTemplate().getItemSlot());
		// 5.0 Classic: 16 bytes. Captura: 01 00 00 00 | 00 00 00 00 | 02 00 00 00 | 00 00 00 00
		writeD(buf, (slots != null && slots.length > 0) ? (int) slots[0].getSlotIdMask() : (int) ItemSlot.MAIN_HAND.getSlotIdMask());
		writeD(buf, 0);
		writeD(buf, item.hasFusionedItem() ? 0x00 : 0x02);
		writeD(buf, 0);
	}

	@Override
	public int getSize() {
		return 16;
	}
}
