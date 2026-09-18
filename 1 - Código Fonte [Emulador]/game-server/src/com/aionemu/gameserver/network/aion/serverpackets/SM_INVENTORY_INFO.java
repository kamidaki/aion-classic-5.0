package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collections;
import java.util.List;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;

/**
 * SM_INVENTORY_INFO (0x001A / S_LOAD_INVENTORY) - Canônico Classic 5.0.
 * Medido na captura oficial: cabeçalho de 9 bytes, itens com ItemInfoBlob 5.0, 0xFFFF no slot e isCloth no final.
 * Pacote de término vazio: exatamente 9 zeros.
 */
public class SM_INVENTORY_INFO extends AionServerPacket {

	private boolean isFirstPacket;
	private List<Item> items;
	private Player player;
	private int npcExpandsSize = 0;
	private int questExpandsSize = 0;

	public SM_INVENTORY_INFO(boolean isFirstPacket, List<Item> items, int npcExpandsSize, int questExpandsSize, Player player) {
		if (items != null) {
			this.items = new java.util.ArrayList<>(items);
			this.items.removeAll(Collections.singletonList(null));
		} else {
			this.items = Collections.emptyList();
		}
		this.isFirstPacket = isFirstPacket;
		this.npcExpandsSize = npcExpandsSize;
		this.questExpandsSize = questExpandsSize;
		this.player = player;
	}

	public SM_INVENTORY_INFO(boolean isFirstPacket, List<Item> items, Player player) {
		this(isFirstPacket, items, player != null ? player.getNpcExpands() : 0, player != null ? player.getQuestExpands() : 0, player);
	}

	public SM_INVENTORY_INFO() {
		this.items = Collections.emptyList();
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if ((items == null || items.isEmpty()) && !isFirstPacket) {
			// 5.0 Classic: 9 zero bytes when empty (wire verified: 00 00 00 00 00 00 00 00 00)
			writeB(new byte[9]);
			return;
		}

		// 5.0 Classic: 9-byte header with count short at offset 7
		// Wire verified: 01 [npc] [quest] 00 00 00 00 [count H]
		writeC(isFirstPacket ? 1 : 0);
		writeC(npcExpandsSize);
		writeC(questExpandsSize);
		writeC(player != null ? player.getItemExpands() : 0);
		writeC(0);
		writeC(0);
		writeC(0);
		writeH(items.size());

		for (Item item : items) {
			writeItemInfo(item);
		}
	}

	private void writeItemInfo(Item item) {
		ItemTemplate itemTemplate = item.getItemTemplate();

		writeD(item.getObjectId());
		writeD(itemTemplate.getTemplateId());

		// In 5.0 Classic, no string localization is written here!
		// The client expects ItemInfoBlob immediately after templateId.
		ItemInfoBlob itemInfoBlob = ItemInfoBlob.getFullBlob(player, item);
		itemInfoBlob.writeMe(getBuf());

		// In 5.0 Classic login packet:
		// Equipped items have slot 0xFFFF (their slot is informed via EQUIPPED_SLOT in ItemInfoBlob).
		// Unequipped items in inventory have their cube slot index.
		writeH(item.isEquipped() ? 0xFFFF : (int) (item.getEquipmentSlot() & 0xFFFF));
		writeC(itemTemplate.isCloth() ? 1 : 0);
	}
}
