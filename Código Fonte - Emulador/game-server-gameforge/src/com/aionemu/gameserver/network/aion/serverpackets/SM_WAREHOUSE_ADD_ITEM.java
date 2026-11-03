package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collections;
import java.util.List;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_WAREHOUSE_ADD_ITEM extends AionServerPacket {

	private int warehouseType;
	private List<Item> items;
	private Player player;
	private ItemAddType addType;

	public SM_WAREHOUSE_ADD_ITEM(Item item, int warehouseType, Player player, ItemAddType addType) {
		this.player = player;
		this.warehouseType = warehouseType;
		this.items = Collections.singletonList(item);
		this.addType = addType;
	}

	/**
	 * Layout 5.0 medido na captura oficial de warehouse: cabecalho de 8 bytes e item com um byte de categoria antes do blob, sem isCloth.
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeC(warehouseType);
		writeC(addType.getMask()); // 0x13 ao depositar
		writeD(0);
		writeH(items.size());

		for (Item item : items)
			writeItemInfo(item);
	}

	private void writeItemInfo(Item item) {
		ItemTemplate itemTemplate = item.getItemTemplate();

		writeD(item.getObjectId());
		writeD(itemTemplate.getTemplateId());
		writeC(0); // categoria do item no warehouse (0x09 stigma, 0x17 enchant...); origem nao identificada, 0 tambem aparece no oficial

		ItemInfoBlob.getFullBlob(player, item).writeMe(getBuf());

		int slot = (int) (item.getEquipmentSlot() & 0xFFFF);
		if (warehouseType == com.aionemu.gameserver.model.items.storage.StorageType.STIGMA.getId()) {
			slot = com.aionemu.gameserver.services.StigmaService.getStigmaSlotIndex(item.getEquipmentSlot());
		}
		writeH(slot);
	}
}
