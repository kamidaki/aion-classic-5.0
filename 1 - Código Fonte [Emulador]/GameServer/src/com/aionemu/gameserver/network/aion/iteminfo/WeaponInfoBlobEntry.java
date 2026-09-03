/*
 * This file is part of aion-lightning <js-emu.ru>.
 *
 *  aion-lightning is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  aion-lightning is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with aion-lightning.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;

public class WeaponInfoBlobEntry extends ItemBlobEntry
{
	WeaponInfoBlobEntry() {
		super(ItemBlobType.SLOTS_WEAPON);
	}
	
	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemSlot[] slots = ItemSlot.getSlotsFor(item.getItemTemplate().getItemSlot());
		// 5.0 Classic: 16 bytes. Captura: 01 00 00 00 | 00 00 00 00 | 02 00 00 00 | 00 00 00 00
		writeD(buf, (slots != null && slots.length > 0) ? slots[0].getSlotIdMask() : ItemSlot.MAIN_HAND.getSlotIdMask());
		writeD(buf, 0);
		writeD(buf, item.hasEffectiveFusion() ? 0x00 : 0x02);
		writeD(buf, 0);
	}
	
	@Override
	public int getSize() {
		return 16;
	}
}