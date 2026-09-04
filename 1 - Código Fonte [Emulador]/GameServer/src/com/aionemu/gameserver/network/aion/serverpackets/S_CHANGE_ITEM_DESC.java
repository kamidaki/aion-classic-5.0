package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;

public class S_CHANGE_ITEM_DESC extends AionServerPacket
{
	private final Player player;
	private final Item item;
	private final ItemUpdateType updateType;
	
	public S_CHANGE_ITEM_DESC(Player player, Item item) {
		this(player, item, ItemUpdateType.DEC_ITEM_USE);
	}
	
	public S_CHANGE_ITEM_DESC(Player player, Item item, ItemUpdateType updateType) {
		this.player = player;
		this.item = item;
		this.updateType = updateType;
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		ItemTemplate itemTemplate = item.getItemTemplate();
		writeD(item.getObjectId());
		// Sem o bloco de nameId, como no resto dos pacotes de item da 5.0. Medido na captura
		// oficial (subida-1-60, sessao 1): 37 amostras, 24 com 15 bytes e 13 com 45. O nosso saia
		// com 23 fixos -- 4 do objectId + 8 do nameId + 9 do blob + 2 da mascara. Tirando os oito,
		// a variante curta fecha em 15 e a cheia em 45, os dois numeros do fio.
		// Este e o PRIMEIRO pacote que o servidor manda em toda operacao de equipar: com ele torto,
		// o cliente desanda logo na primeira resposta de cada equipar e desequipar.
		ItemInfoBlob itemInfoBlob;
		switch (updateType) {
			case EQUIP_UNEQUIP:
				itemInfoBlob = new ItemInfoBlob(player, item);
				itemInfoBlob.addBlobEntry(ItemBlobType.EQUIPPED_SLOT);
			break;
			case CHARGE:
				itemInfoBlob = new ItemInfoBlob(player, item);
				itemInfoBlob.addBlobEntry(ItemBlobType.CONDITIONING_INFO);
			default:
				itemInfoBlob = ItemInfoBlob.getFullBlob(player, item);
			break;
		}
		itemInfoBlob.writeMe(getBuf());
		if (updateType.isSendable())
			writeH(updateType.getMask());
	}
}