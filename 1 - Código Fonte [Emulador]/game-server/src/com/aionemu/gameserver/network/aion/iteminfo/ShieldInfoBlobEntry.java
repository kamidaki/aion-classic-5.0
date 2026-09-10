package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

public class ShieldInfoBlobEntry extends ItemBlobEntry {

	ShieldInfoBlobEntry() {
		super(ItemBlobType.SLOTS_SHIELD);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemSlot slot = ItemSlot.getSlotFor(item.getItemTemplate().getItemSlot());
		writeQ(buf, slot != null ? slot.getSlotIdMask() : ItemSlot.SUB_HAND.getSlotIdMask());
		writeC(buf, item.getItemTemplate().isItemDyePermitted() ? 1 : 0);
		int color = item.getItemColor() != null ? item.getItemColor() : 0;
		writeC(buf, (color & 0xFF0000) >> 16);
		writeC(buf, (color & 0xFF00) >> 8);
		writeC(buf, (color & 0xFF));
		// 5.0 Classic: 20 bytes (u64 slot + 4 bytes dye + 8 bytes padding).
		writeB(buf, new byte[8]);
	}

	@Override
	public int getSize() {
		return 20;
	}
}
