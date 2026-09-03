/*
 * This file is part of aion-unique <www.aion-unique.com>.
 *
 *  aion-unique is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  aion-unique is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with aion-unique.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.GodStone;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import java.util.List;

public class S_WIELD extends AionServerPacket
{
    public int playerId;
    public int size;
    public List<Item> items;
	
    public S_WIELD(int playerId, List<Item> items) {
        this.playerId = playerId;
        this.items = items;
        this.size = items != null ? items.size() : 0;
    }
	
    @Override
    protected void writeImpl(AionConnection con) {
        writeD(playerId);
        writeD(0); // u32 zero confirmado no PCAP
        int mask = 0;
        for (Item item : items) {
            mask |= item.getEquipmentSlot();
        }

        writeD(mask); // u32 mask na 5.0

        for (int i = 0; i < 32; i++) {
            int bit = 1 << i;
            if ((mask & bit) != 0) {
                Item matchedItem = null;
                for (Item item : items) {
                    if ((item.getEquipmentSlot() & bit) != 0) {
                        matchedItem = item;
                        break;
                    }
                }
                if (matchedItem != null) {
                    writeD(matchedItem.getItemSkinTemplate().getTemplateId());
                    GodStone godStone = matchedItem.getGodStone();
                    writeD(godStone != null ? godStone.getItemId() : 0);
                    writeD(matchedItem.getItemColor());
                    writeB(new byte[8]);
                } else {
                    writeB(new byte[20]);
                }
            }
        }
    }
}