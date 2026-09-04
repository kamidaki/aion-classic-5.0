/*
 * This file is part of aion-unique <aionunique.com>.
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
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;

import java.util.Collection;
import java.util.Collections;

/**
 * @author kosyachok
 */
public class S_LOAD_WAREHOUSE extends AionServerPacket {

	private int warehouseType;
	private Collection<Item> itemList;
	private boolean firstPacket;
	private int expandLvl;
	private Player player;

	public S_LOAD_WAREHOUSE(Collection<Item> items, int warehouseType, int expandLvl, boolean firstPacket, Player player) {
		this.warehouseType = warehouseType;
		this.expandLvl = expandLvl;
		this.firstPacket = firstPacket;
		if (items == null)
			this.itemList = Collections.emptyList();
		else
			this.itemList = items;
		this.player = player;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(warehouseType);
		writeC(firstPacket ? 1 : 0);
		writeC(expandLvl); // warehouse expand (0 - 9)
		writeH(0);
		writeH(itemList.size());
		for (Item item : itemList)
			writeItemInfo(item);
	}

	private void writeItemInfo(Item item) {
		ItemTemplate itemTemplate = item.getItemTemplate();

		writeD(item.getObjectId());
		writeD(itemTemplate.getTemplateId());
		// Sem writeC(0) e sem o bloco writeNameId: a 5.0 vai do templateId direto para o
		// ItemInfoBlob. Eram nove bytes a mais por item, e o cliente lia o 0x0024 do nameId
		// como tamanho do blob -- dai a quantidade errada e a janela fechando sozinha.
		// Mesmo defeito que o S_LOAD_INVENTORY ja tinha corrigido e que o S_ADD_INVENTORY
		// carregava ate a captura mostrar o layout certo.

		ItemInfoBlob itemInfoBlob = ItemInfoBlob.getFullBlob(player, item);
		itemInfoBlob.writeMe(getBuf());

		writeH((int) (item.getEquipmentSlot() & 0xFFFF)); // FF FF equipment
		// Byte final do bloco de item, igual ao S_LOAD_INVENTORY. Sem ele cada item fica um byte
		// curto e o pacote do login desanda a partir do segundo.
		writeC(itemTemplate.isCloth() ? 1 : 0);
	}
}
