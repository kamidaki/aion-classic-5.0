package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_INVENTORY_UPDATE_ITEM extends AionServerPacket {

	private final Player player;
	private final Item item;
	private final ItemUpdateType updateType;

	public SM_INVENTORY_UPDATE_ITEM(Player player, Item item) {
		this(player, item, ItemUpdateType.STATS_CHANGE); // troca de informação do item: o oficial manda motivo 0
	}

	public SM_INVENTORY_UPDATE_ITEM(Player player, Item item, ItemUpdateType updateType) {
		this.player = player;
		this.item = item;
		this.updateType = updateType;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(item.getObjectId());

		ItemInfoBlob itemInfoBlob;
		switch (updateType) {
			case EQUIP_UNEQUIP:
				itemInfoBlob = new ItemInfoBlob(player, item);
				itemInfoBlob.addBlobEntry(ItemBlobType.EQUIPPED_SLOT);
				itemInfoBlob.writeMe(getBuf());
				break;
			case CHARGE:
				itemInfoBlob = new ItemInfoBlob(player, item);
				itemInfoBlob.addBlobEntry(ItemBlobType.CONDITIONING_INFO);
				itemInfoBlob.writeMe(getBuf());
				break;

			default:
				itemInfoBlob = ItemInfoBlob.getFullBlob(player, item);
				itemInfoBlob.writeMe(getBuf());
				// Classic 5.0 wire: [D motivo][C 0] depois do blob. Motivo sem captura vai 0 (ver ItemUpdateType).
				// As variantes de equipar (entrada 0x06) e de carga não têm trailer: o oficial manda 15 e 11 bytes.
				writeD(updateType.getReason());
				writeC(0);
				break;
		}
	}
}
