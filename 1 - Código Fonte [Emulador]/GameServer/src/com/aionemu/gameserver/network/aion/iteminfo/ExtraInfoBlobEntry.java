package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;

/**
 * Etiqueta 0x12: entrada nova na 5.0 Classic, ausente nas versoes anteriores.
 * <p>
 * Na captura oficial (01_Login_World) ela aparece em todo item equipavel, sempre
 * com dois bytes zerados, entre os soquetes (0x0B) e o bloco geral (0x00). Sem
 * ela o cliente le os dois bytes seguintes como parte do bloco geral e todo o
 * resto do inventario desalinha.
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
