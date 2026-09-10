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
		// Classic 5.0: envia o slot completo em uint64 (ex: 3 para 2H Set 1, 0x60000 para 2H Set 2).
		writeQ(buf, item.isEquipped() ? item.getEquipmentSlot() : 0L);
	}

	@Override
	public int getSize() {
		return 8;
	}
}
