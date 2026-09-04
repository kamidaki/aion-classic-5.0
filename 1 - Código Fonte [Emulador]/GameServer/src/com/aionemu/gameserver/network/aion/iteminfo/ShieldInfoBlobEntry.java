package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;

/**
 * This blob is sent for shields. It keeps info about slots that shield can be equipped to.
 *
 * @modified Rolandas
 */
public class ShieldInfoBlobEntry extends ItemBlobEntry{

	ShieldInfoBlobEntry() {
		super(ItemBlobType.SLOTS_SHIELD);
	}

	@Override
	public
	void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;

		ItemSlot slot = ItemSlot.getSlotFor(item.getItemTemplate().getItemSlot());
		writeQ(buf, slot != null ? slot.getSlotIdMask() : ItemSlot.SUB_HAND.getSlotIdMask());
		writeC(buf, item.getItemTemplate().isItemDyePermitted() ? 1 : 0);
		writeC(buf, (item.getItemColor() & 0xFF0000) >> 16);
		writeC(buf, (item.getItemColor() & 0xFF00) >> 8);
		writeC(buf, (item.getItemColor() & 0xFF));
	}

	@Override
	public int getSize() {
		return 12;
	}
}
