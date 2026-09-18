package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collections;
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

	public SM_INVENTORY_ADD_ITEM(Item item, Player player, ItemAddType addType) {
		this(Collections.singletonList(item), player, addType);
	}

	public SM_INVENTORY_ADD_ITEM(List<Item> items, Player player, ItemAddType addType) {
		this.player = player;
		this.items = items;
		this.addType = addType;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		// Classic 5.0: 6 zero bytes header followed by count short
		if (addType == ItemAddType.CRUSH_RESULT) {
			writeD(addType.getMask());
			writeC(0);
			writeC(1);
		} else {
			writeB(new byte[6]);
		}
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

		// Classic 5.0 wire verified (pacotes oficiais S_ADD_INVENTORY):
		// O tail_slot enviado ao adicionar itens ao cubo é sempre 0xFFFF (65535).
		// Se o servidor enviar um número de slot diferente de 0xFFFF (como 2 para o 2º slot do cubo),
		// o cliente Aion interpreta como slot de equipamento (2 = SUB_HAND), substituindo a Off-Hand!
		writeH(0xFFFF);
		writeC(item.getItemTemplate().isCloth() ? 1 : 0);
	}
}
