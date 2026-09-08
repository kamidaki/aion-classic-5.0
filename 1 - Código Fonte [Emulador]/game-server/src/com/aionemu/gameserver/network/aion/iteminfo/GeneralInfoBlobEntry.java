package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

/**
 * GeneralInfoBlobEntry (0x00) - Classic 5.0
 * Medido na captura oficial: 33 bytes (fecho com u16=0 e u16=15).
 */
public class GeneralInfoBlobEntry extends ItemBlobEntry {

	GeneralInfoBlobEntry() {
		super(ItemBlobType.GENERAL_INFO);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		writeH(buf, item.getItemMask());
		writeQ(buf, item.getItemCount());
		writeS(buf, item.getItemCreator());
		writeC(buf, 0);
		writeD(buf, item.getExpireTimeRemaining());
		writeD(buf, 0);
		writeD(buf, item.getTemporaryExchangeTimeRemaining());
		writeD(buf, 0);
		// 5.0 Classic: a entrada tem 33 bytes e fecha com u16 = 15.
		writeH(buf, 0);
		writeH(buf, 15);
	}

	@Override
	public int getSize() {
		String creator = ownerItem.getItemCreator();
		return 31 + (creator != null ? creator.length() * 2 : 0) + 2;
	}
}
