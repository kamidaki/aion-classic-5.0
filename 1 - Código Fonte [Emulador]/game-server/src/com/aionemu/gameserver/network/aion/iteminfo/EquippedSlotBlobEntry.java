package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

public class EquippedSlotBlobEntry extends ItemBlobEntry {

	EquippedSlotBlobEntry() {
		super(ItemBlobType.EQUIPPED_SLOT);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		long slot = item.getEquipmentSlot();
		if ((slot & ItemSlot.MAIN_OR_SUB.getSlotIdMask()) == ItemSlot.MAIN_OR_SUB.getSlotIdMask()) {
			slot = ItemSlot.MAIN_HAND.getSlotIdMask();
		} else if ((slot & ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask()) == ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask()) {
			slot = ItemSlot.MAIN_OFF_HAND.getSlotIdMask();
		}
		// 5.0 Classic: a mascara de slot e u64 (8 bytes).
		writeQ(buf, item.isEquipped() ? slot : 0);
	}

	@Override
	public int getSize() {
		return 8;
	}
}
