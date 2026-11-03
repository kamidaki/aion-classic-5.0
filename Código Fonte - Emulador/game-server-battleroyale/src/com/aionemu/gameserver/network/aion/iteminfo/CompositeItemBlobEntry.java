package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.stats.calc.functions.StatRateFunction;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;
import com.aionemu.gameserver.utils.idfactory.IDFactory;

/**
 * CompositeItemBlobEntry (0x0E) - Canônico Aion Classic 5.0 (EU).
 * Validado diretamente no tráfego oficial do Wireshark (pacotes 3271, 5833, 5834, 7784 e 8956).
 *
 * Estrutura Classic 5.0:
 * - Sem fusão (Arma 2H limpa):
 *   writeD(0); // templateId = 0
 *   writeB(new byte[458]); // corpo zerado canônico
 *   Total de payload = 462 bytes (463 com o EID 0x0E).
 *
 * - Com fusão:
 *   writeD(templateId); // 4 bytes (offset 1..4)
 *   writeD(objectId);   // 4 bytes (offset 5..8)
 *   writeC(0);          // 1 byte  (offset 9)
 *   writeH(1);          // 2 bytes (offset 10..11)
 *   writeC(enchant);    // 1 byte  (offset 12)
 *   writeD(skinId);     // 4 bytes (offset 13..16)
 *   writeFusionStones;  // 24 bytes (offset 17..40)
 *   writeB(new byte[411]); // 411 bytes de zeros (offset 41..451)
 *   writeD(modCount);   // 4 bytes (offset 452..455)
 *   para cada modifier: // 7 bytes por modifier
 *     writeH(mask);
 *     writeD(value);
 *     writeC(isRate ? 1 : 0);
 *   writeB(new byte[7]); // 7 bytes de zeros de fechamento
 *   Total de payload = 462 + bonusModifiers.size() * 7 bytes.
 */
public class CompositeItemBlobEntry extends ItemBlobEntry {

	private static final int BASE_PAYLOAD_SIZE = 462;

	CompositeItemBlobEntry() {
		super(ItemBlobType.COMPOSITE_ITEM);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		ItemTemplate fusionTemplate = item.getFusionedItemTemplate();

		if (fusionTemplate == null) {
			writeD(buf, 0);
			writeB(buf, new byte[BASE_PAYLOAD_SIZE - 4]);
			return;
		}

		Item fusionedItem = item.getFusionedItem();
		int fusionObjId = fusionedItem != null ? fusionedItem.getObjectId() : IDFactory.getInstance().nextId();
		int fusionSkinId = fusionedItem != null && fusionedItem.getItemSkinTemplate() != null
			? fusionedItem.getItemSkinTemplate().getTemplateId()
			: fusionTemplate.getTemplateId();

		writeD(buf, fusionTemplate.getTemplateId());
		writeD(buf, fusionObjId);
		writeC(buf, 0);
		writeH(buf, 1);
		writeC(buf, item.getFusionedItemEnchant());
		writeD(buf, fusionSkinId);
		writeFusionStones(buf);
		writeB(buf, new byte[411]);

		List<StatFunction> bonusMods = getBonusModifiers(fusionTemplate);
		writeD(buf, bonusMods.size());
		for (StatFunction mod : bonusMods) {
			writeH(buf, mod.getName().getItemStoneMask());
			writeD(buf, mod.getValue() * mod.getName().getSign());
			writeC(buf, mod instanceof StatRateFunction ? 1 : 0);
		}
		writeB(buf, new byte[7]);
	}

	private void writeFusionStones(ByteBuffer buf) {
		Item item = ownerItem;

		if (item.hasFusionStones()) {
			Set<ManaStone> itemStones = item.getFusionStones();
			ManaStone[] slots = new ManaStone[6];
			for (ManaStone ms : itemStones) {
				if (ms.getSlot() >= 0 && ms.getSlot() < 6) {
					slots[ms.getSlot()] = ms;
				}
			}

			// 6 shorts para máscaras das manastones da arma secundária (Big-Endian canônico Classic 5.0)
			for (int i = 0; i < 6; i++) {
				StatFunction modifier = slots[i] != null ? slots[i].getFirstModifier() : null;
				int mask = modifier != null ? modifier.getName().getItemStoneMask() : 0;
				buf.putShort(Short.reverseBytes((short) mask));
			}

			// 6 shorts para valores das manastones da arma secundária (Big-Endian canônico Classic 5.0)
			for (int i = 0; i < 6; i++) {
				StatFunction modifier = slots[i] != null ? slots[i].getFirstModifier() : null;
				int value = modifier != null ? modifier.getValue() : 0;
				buf.putShort(Short.reverseBytes((short) value));
			}
		} else {
			skip(buf, 24);
		}
	}

	private List<StatFunction> getBonusModifiers(ItemTemplate fusionTemplate) {
		if (fusionTemplate == null || fusionTemplate.getModifiers() == null) {
			return Collections.emptyList();
		}
		List<StatFunction> bonusMods = new ArrayList<>();
		for (StatFunction mod : fusionTemplate.getModifiers()) {
			if (mod.isBonus() && !mod.hasConditions()) {
				bonusMods.add(mod);
			}
		}
		return bonusMods;
	}

	@Override
	public int getSize() {
		ItemTemplate fusionTemplate = ownerItem.getFusionedItemTemplate();
		if (fusionTemplate == null) {
			return BASE_PAYLOAD_SIZE;
		}
		return BASE_PAYLOAD_SIZE + getBonusModifiers(fusionTemplate).size() * 7;
	}
}
