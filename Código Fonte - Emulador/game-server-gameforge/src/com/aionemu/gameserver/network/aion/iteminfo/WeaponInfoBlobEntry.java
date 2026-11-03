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
		if (item.getItemTemplate().isTwoHandWeapon()) {
			// Retail Classic 5.0: Two-handed weapons send MAIN_OR_SUB (3L) + 0L.
			writeQ(buf, ItemSlot.MAIN_OR_SUB.getSlotIdMask());
			writeQ(buf, 0L);
		} else {
			// Retail Classic 5.0: One-handed weapons send MAIN_HAND (1L) + SUB_HAND (2L).
			writeQ(buf, ItemSlot.MAIN_HAND.getSlotIdMask());
			writeQ(buf, ItemSlot.SUB_HAND.getSlotIdMask());
		}
	}

	@Override
	public int getSize() {
		return 16;
	}
}
