package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.ItemStorage;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_INVENTORY_ADD_ITEM extends AionServerPacket {

	private final List<Item> items;
	private Player player;
	private ItemAddType addType;

	public SM_INVENTORY_ADD_ITEM(List<Item> items, Player player, ItemAddType addType) {
		this.player = player;
		this.items = items;
		this.addType = addType;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		// Classic 5.0: 6 zero bytes header followed by count short
		writeB(new byte[6]);
		writeH(items.size());
		for (Item item : items)
			writeItemInfo(item);
	}

	private void writeItemInfo(Item item) {
		ItemTemplate itemTemplate = item.getItemTemplate();

		writeD(item.getObjectId());
		writeD(itemTemplate.getTemplateId());

		// In 5.0 Classic, no string localization is written here!
		ItemInfoBlob.getFullBlob(player, item).writeMe(getBuf());

		writeH(item.isEquipped() ? 0xFFFF : (int) (item.getEquipmentSlot() & 0xFFFF));
		writeC(item.getItemTemplate().isCloth() ? 1 : 0);
	}
}
