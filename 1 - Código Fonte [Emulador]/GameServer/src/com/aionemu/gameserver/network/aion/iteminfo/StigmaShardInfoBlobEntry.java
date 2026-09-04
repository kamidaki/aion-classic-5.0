package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;


public class StigmaShardInfoBlobEntry extends ItemBlobEntry {

	public StigmaShardInfoBlobEntry() {
		super(ItemBlobType.STIGMA_SHARD);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		writeD(buf, 0);
	}

	@Override
	public int getSize() {
		return 4;
	}

}
