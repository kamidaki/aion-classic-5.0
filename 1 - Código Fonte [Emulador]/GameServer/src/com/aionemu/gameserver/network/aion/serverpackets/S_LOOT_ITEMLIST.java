package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.drop.DropItem;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import javolution.util.FastList;
import org.slf4j.LoggerFactory;

import java.util.Set;

public class S_LOOT_ITEMLIST extends AionServerPacket {
    private int targetObjectId;
    private FastList<DropItem> dropItems;

    public S_LOOT_ITEMLIST(int targetObjectId, Set<DropItem> setItems, Player player) {
        this.targetObjectId = targetObjectId;
        this.dropItems = new FastList<DropItem>();
        if (setItems == null) {
            LoggerFactory.getLogger(S_LOOT_ITEMLIST.class).warn("null Set<DropItem>, skip");
            return;
        }
        for (DropItem item : setItems) {
            if (item.getPlayerObjId() == 0 || player.getObjectId() == item.getPlayerObjId())
                dropItems.add(item);
        }
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(targetObjectId);
        writeH(dropItems.size());
        for (DropItem dropItem : dropItems) {
            writeD(dropItem.getIndex());
            writeD(dropItem.getItemId());
            writeD((int) dropItem.getCount());
            writeC(dropItem.getOptionalSocket());
            writeC(dropItem.getDropTemplate().isTradeable() ? 0 : 1);
        }
        FastList.recycle(dropItems);
    }
}