/*
 * This file is part of aion-unique <aion-unique.com>.
 *
 * aion-unique is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * aion-unique is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with aion-unique.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;

import java.util.Collections;
import java.util.List;

/**
 * In this packet Server is sending Inventory Info
 * 
 * @author -Nemesiss-
 * @updater alexa026
 * @finisher Avol ;d modified by ATracer
 * @fixedby -Nemesiss- :D
 */
public class S_LOAD_INVENTORY extends AionServerPacket {

	public static final int EMPTY = 0;
	public static final int FULL = 1;
	public int npcExpandsSize = 0;
	public int questExpandsSize = 0;

	private List<Item> items;
	private Player player;

	public int packetType = FULL;
	private boolean isFirstPacket;

	/**
	 * @param items
	 */
	public S_LOAD_INVENTORY(boolean isFirstPacket, List<Item> items, int npcExpandsSize, int questExpandsSize, Player player) {
        // this should prevent client crashes but need to discover when item is null
        items.removeAll(Collections.singletonList(null));
        this.isFirstPacket = isFirstPacket;
        this.items = items;
        this.npcExpandsSize = npcExpandsSize;
        this.questExpandsSize = questExpandsSize;
        this.player = player;
    }

	/**
	 * @param isEmpty
	 */
	public S_LOAD_INVENTORY() {
		this.packetType = EMPTY;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		if (this.packetType == EMPTY) {
			// 5.0 Classic: o cabecalho tem 9 bytes e o pacote vazio sao 9 zeros
			// (provado na captura oficial 01_Login_World).
			writeB(new byte[9]);
			return;
		}

		// something wrong with cube part.
		// 5.0 Classic: cabecalho de 9 bytes com a contagem no offset 7.
		// Na captura oficial: 01 00 00 00 00 00 00 | 09 00
		writeC(isFirstPacket ? 1 : 0);
		writeC(npcExpandsSize); // cube size from npc (so max 5 for now)
		writeC(questExpandsSize); // cube size from quest (so max 2 for now)
		writeC(0);
		writeC(0);
		writeC(0);
		writeC(0);
		writeH(items.size()); // number of entries

		for (Item item : items)
			writeItemInfo(item);
	}

	private void writeItemInfo(Item item)
	{
		ItemTemplate itemTemplate = item.getItemTemplate();

		writeD(item.getObjectId());
		writeD(itemTemplate.getTemplateId());
		// A 5.0 nao tem o bloco writeNameId (0x24 + nameId + 0x00) aqui: o cliente
		// leria o 0x0024 como tamanho do blob e o pacote desandava no primeiro item.

		ItemInfoBlob itemInfoBlob = ItemInfoBlob.getFullBlob(player, item);
		itemInfoBlob.writeMe(getBuf());

		writeH(item.isEquipped() ? -1 : item.getEquipmentSlot());
		writeC(itemTemplate.isCloth() ? 1 : 0);
	}
}