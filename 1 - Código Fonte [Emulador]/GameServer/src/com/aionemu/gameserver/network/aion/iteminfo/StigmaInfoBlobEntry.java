package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;

public class StigmaInfoBlobEntry extends ItemBlobEntry
{
	StigmaInfoBlobEntry() {
		super(ItemBlobType.STIGMA_INFO);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		writeH(buf, item.getItemTemplate().getStigma().getSkillid());
		writeD(buf, 0);
		writeH(buf, 0);
		writeD(buf, 0x3c);
		skip(buf, 160);
		writeC(buf, 1);
		skip(buf, 85);
	}

	@Override
	public int getSize() {
		return 258;
	}
}