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
		// 5.0 Classic: 20 bytes, [Q slot][Q 0][C tingido][R][G][B]. Nas capturas o byte logo depois do slot é 0 nas 424 armaduras, e a tinta
		// fica no fim (71 tingidas, ex. 00 10 .. 00 01 1f 87 f5; o torso tingido pelo Wardrobe veio 08 00 .. 00 01 19 8d 94).
		writeQ(buf, (slots != null && slots.length > 0) ? slots[0].getSlotIdMask() : 0);
		writeQ(buf, 0);
		writeDyeInfo(buf, item.getItemColor());
	}

	@Override
	public int getSize() {
		return 20;
	}
}
