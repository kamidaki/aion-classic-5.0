package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;

/**
 * Etiqueta 0x12: entrada nova na 5.0 Classic, ausente nas versoes anteriores.
 * Na captura oficial ela aparece em todo item equipavel, sempre com dois bytes zerados.
 */
public class ExtraInfoBlobEntry extends ItemBlobEntry {

	ExtraInfoBlobEntry() {
		super(ItemBlobType.EXTRA_INFO);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		writeH(buf, 0);
	}

	@Override
	public int getSize() {
		return 2;
	}
}
