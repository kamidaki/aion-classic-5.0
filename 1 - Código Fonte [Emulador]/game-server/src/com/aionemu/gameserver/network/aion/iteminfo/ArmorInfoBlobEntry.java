package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

public class ArmorInfoBlobEntry extends ItemBlobEntry {

	ArmorInfoBlobEntry() {
		super(ItemBlobType.SLOTS_ARMOR);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemSlot[] slots = ItemSlot.getSlotsFor(item.getItemTemplate().getItemSlot());
		writeQ(buf, (slots != null && slots.length > 0) ? slots[0].getSlotIdMask() : 0);
		writeC(buf, item.getItemTemplate().isItemDyePermitted() ? 1 : 0);
		int color = item.getItemColor() != null ? item.getItemColor() : 0;
		writeC(buf, (color & 0xFF0000) >> 16);
		writeC(buf, (color & 0xFF00) >> 8);
		writeC(buf, (color & 0xFF));
		// 5.0 Classic: a entrada tem 20 bytes. Captura: u64 slot + 12 bytes (4 de tintura + 8 zeros).
		writeB(buf, new byte[8]);
	}

	@Override
	public int getSize() {
		return 20;
	}
}
