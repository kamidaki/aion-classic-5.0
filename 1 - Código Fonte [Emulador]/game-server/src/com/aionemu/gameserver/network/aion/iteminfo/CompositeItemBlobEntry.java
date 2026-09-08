package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;
import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

public class CompositeItemBlobEntry extends ItemBlobEntry {

	CompositeItemBlobEntry() {
		super(ItemBlobType.COMPOSITE_ITEM);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemTemplate fusionTemplate = item.getFusionedItemTemplate();
		writeD(buf, fusionTemplate != null ? fusionTemplate.getTemplateId() : 0);
		writeFusionStones(buf);
		writeC(buf, item.hasOptionalFusionSocket() ? item.getFusionedItemOptionalSockets() : 0);
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
		} else {
			skip(buf, 24);
		}
	}

	@Override
	public int getSize() {
		return 29;
	}
}
