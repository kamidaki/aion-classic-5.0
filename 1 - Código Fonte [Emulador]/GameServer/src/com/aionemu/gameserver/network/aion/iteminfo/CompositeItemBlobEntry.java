package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Set;

public class CompositeItemBlobEntry extends ItemBlobEntry
{
	CompositeItemBlobEntry() {
		super(ItemBlobType.COMPOSITE_ITEM);
	}
	
	@Override
    public void writeThisBlob(ByteBuffer buf) {
        Item item = ownerItem;
        // 5.0 Classic: also reports the secondary weapon fused through the off hand,
        // so the tooltip shows the info of both weapons.
        ItemTemplate fusionTemplate = item.getEffectiveFusionTemplate();
        writeD(buf, fusionTemplate != null ? fusionTemplate.getTemplateId() : 0);
        writeFusionStones(buf);
        writeC(buf, item.hasOptionalFusionSocket() ? item.getOptionalFusionSocket() : 0);
    }

    private void writeFusionStones(ByteBuffer buf) {
        Item item = ownerItem;
        int count = 0;
        

        if (item.hasFusionStones()) {
            Set<ManaStone> itemStones = item.getFusionStones();

            for (ManaStone itemStone : itemStones) {
                if (count == 6)
                    break;

                StatFunction modifier = itemStone.getFirstModifier();
                if (modifier != null) {
                    count++;
                    writeH(buf, modifier.getName().getItemStoneMask());
                    writeH(buf, modifier.getValue());
                }
            }
            skip(buf, (6 - count) * 4);
        }
        else {
            skip(buf, 24);
        }
        // for now max 6 stones - write some junk
    }
	
	@Override
	public int getSize() {
		return 29;
	}
}