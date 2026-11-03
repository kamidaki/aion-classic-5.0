package com.aionemu.gameserver.network.aion.serverpackets;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

/**
 * Detalhe do item nos pacotes da Global Auction House: 441 bytes com o mesmo corpo da entrada 0x0B (mana sockets) do blob de item, sem o
 * id da entrada. Nas capturas: skin no offset 2, a cauda B7 D6 / 02 / 01 / 01 / 44 / 01 e o valor de 3 bytes no offset 430 iguais aos do
 * inventário. Item que não é equipamento vem só com a skin (ou zerado, ou com lixo de memória nos anúncios já vendidos): o cliente não lê.
 */
final class GlobalTradeItemDetail {

	static final int SIZE = 441;
	private static final long DAY_MILLIS = 24L * 60 * 60 * 1000;

	private GlobalTradeItemDetail() {
	}

	/**
	 * @param item
	 *          null quando o item já não existe (anúncio vendido, o item é do comprador)
	 */
	static void write(ByteBuffer buf, Item item, int itemId) {
		int start = buf.position();
		if (item != null && isEquipment(item)) {
			ItemInfoBlob.newBlobEntry(ItemBlobType.MANA_SOCKETS, null, item).writeThisBlob(buf);
		} else {
			buf.put((byte) 0);
			buf.put((byte) 0);
			buf.putInt(itemId);
		}
		int written = buf.position() - start;
		if (written > SIZE)
			throw new IllegalStateException("Global trade item detail with " + written + " bytes");
		buf.put(new byte[SIZE - written]);
	}

	/**
	 * Anúncio do próprio jogador, 473 bytes, no S_GLOBAL_TRADE_MYLIST e no S_GLOBAL_TRADE_COMMIT (captura de 2026-09-21):
	 * [Q anúncio][D item][Q preço][D quantidade][D 0][C dias restantes][441 bytes de detalhe][3 bytes 0]. Os dias saem inteiros para baixo:
	 * 8 no registro e 7 minutos depois, no mesmo anúncio.
	 */
	static void writeRegistered(ByteBuffer buf, GlobalTradeListing listing) {
		buf.putLong(listing.getId());
		buf.putInt(listing.getItemId());
		buf.putLong(listing.getPrice());
		buf.putInt((int) listing.getCount());
		buf.putInt(0);
		buf.put((byte) Math.max(0, (listing.getExpireTime() - System.currentTimeMillis() + 999) / DAY_MILLIS));
		write(buf, listing.getItem(), listing.getItemId());
		buf.put(new byte[3]);
	}

	private static boolean isEquipment(Item item) {
		ItemTemplate template = item.getItemTemplate();
		return template.isArmor() || template.isWeapon() || template.isStigma()
			|| template.getItemGroup() != null && template.getItemGroup().getValidEquipmentSlots() != 0;
	}
}
