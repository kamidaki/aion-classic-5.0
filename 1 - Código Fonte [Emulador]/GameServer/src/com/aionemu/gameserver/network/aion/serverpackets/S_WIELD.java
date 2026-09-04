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