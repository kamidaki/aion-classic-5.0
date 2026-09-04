package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;

/**
 * This blob entry is sent with ALL items. (unless partial blob is constructed, ie: sending equip slot only) It is the
 * first and only block for non-equipable items, and the last blob for EquipableItems
 * 
 * @modified Rolandas
 */
public class GeneralInfoBlobEntry extends ItemBlobEntry {
	GeneralInfoBlobEntry() {
		super(ItemBlobType.GENERAL_INFO);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {// TODO what with kinah?
		Item item = ownerItem;
		writeH(buf, item.getItemMask(owner));
		writeQ(buf, item.getItemCount());
		writeS(buf, item.getItemCreator());// Creator name
		writeC(buf, 0);
		writeD(buf, item.getExpireTimeRemaining()); // Disappears time
		writeD(buf, 0);
		writeD(buf, item.getTemporaryExchangeTimeRemaining());
		writeD(buf, 0);
		// 5.0 Classic: a entrada tem 33 bytes e fecha com u16 = 15.
		// Captura (arma, criador vazio): 3c 88 | 01 00 00 00 00 00 00 00 | 21 zeros | 0f 00
		writeH(buf, 0);
		writeH(buf, 15);
	}

	@Override
	public int getSize() {
		return 31 + ownerItem.getItemCreator().length() * 2 + 2;
	}
}
