package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemStone;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;
import java.util.Set;

/**
 * ManaStoneInfoBlobEntry (0x0B) - Classic 5.0.
 * A entrada tem exatamente 441 bytes (60 bytes de corpo + 381 bytes da cauda canonica 5.0).
 * Comprovado em capturas Wireshark oficiais do Classic 5.0.
 */
public class ManaStoneInfoBlobEntry extends ItemBlobEntry {

	private static final int BODY_SIZE = 60;
	private static final int TOTAL_SIZE = 441;

	ManaStoneInfoBlobEntry() {
		super(ItemBlobType.MANA_SOCKETS);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Item item = ownerItem;
		writeC(buf, item.isSoulBound() ? 1 : 0);
		writeC(buf, item.getEnchantLevel());
		writeD(buf, item.getItemSkinTemplate().getTemplateId());
		writeC(buf, item.getOptionalSockets());

		writeItemStones(buf);
		ItemStone god = item.getGodStone();
		writeD(buf, god == null ? 0 : god.getItemId());

		// Cor como [C tingido][R][G][B] (71 itens tingidos nas capturas, ex. 01 1f 87 f5). Os dois bytes do Wardrobe valem 1 só em item com visual
		// aplicado pelo guarda-roupa (62 de 62) e 0 no visual de remodelagem por NPC (247); o C 0xFA de remoção os zera.
		int dyeExpiration = item.getColorTimeLeft();
		writeDyeInfo(buf, item.getItemColor());
		writeC(buf, item.isWardrobeSkin() ? 1 : 0);
		writeD(buf, 0); // unk 1.5.1.9
		writeD(buf, dyeExpiration > 0 && item.getColorExpireTime() > 0 && item.getItemTemplate().isItemDyePermitted() ? dyeExpiration : 0);
		writeC(buf, item.isWardrobeSkin() ? 1 : 0);
		writeC(buf, 0);
		writeH(buf, 0);

		writeD(buf, 0); // 2.4
		writeD(buf, 0); // 2.8

		writeTail50(buf);
	}

	private void writeTail50(ByteBuffer buf) {
		byte[] tail = new byte[TOTAL_SIZE - BODY_SIZE];
		// offset 60: skill de equipamento (Assign Skill on Loot / Reassign); 130 de 130 itens das capturas com uma skill do próprio conjunto
		int skillId = ownerItem.getBuffSkill();
		tail[0] = (byte) skillId;
		tail[1] = (byte) (skillId >> 8);
		tail[2] = (byte) (skillId >> 16);
		tail[3] = (byte) (skillId >> 24);
		tail[196 - BODY_SIZE] = (byte) 0xB7;
		tail[197 - BODY_SIZE] = (byte) 0xD6;
		tail[268 - BODY_SIZE] = 0x02;
		tail[286 - BODY_SIZE] = 0x01;
		tail[304 - BODY_SIZE] = 0x01;
		tail[324 - BODY_SIZE] = 0x44;
		tail[376 - BODY_SIZE] = 0x01;
		tail[430 - BODY_SIZE] = (byte) 0x88;
		tail[431 - BODY_SIZE] = 0x4C;
		tail[432 - BODY_SIZE] = 0x01;
		writeB(buf, tail);
	}

	private void writeItemStones(ByteBuffer buf) {
		Item item = ownerItem;

		if (item.hasManaStones()) {
			Set<ManaStone> itemStones = item.getItemStones();
			ManaStone[] slots = new ManaStone[6];
			for (ManaStone ms : itemStones) {
				if (ms.getSlot() >= 0 && ms.getSlot() < 6) {
					slots[ms.getSlot()] = ms;
				}
			}

			for (int i = 0; i < 6; i++) {
				StatFunction modifier = slots[i] != null ? slots[i].getFirstModifier() : null;
				int mask = modifier != null ? modifier.getName().getItemStoneMask() : 0;
				writeH(buf, mask);
			}

			for (int i = 0; i < 6; i++) {
				StatFunction modifier = slots[i] != null ? slots[i].getFirstModifier() : null;
				int value = modifier != null ? modifier.getValue() : 0;
				writeH(buf, value);
			}
		} else {
			skip(buf, 24);
		}
	}

	@Override
	public int getSize() {
		return TOTAL_SIZE;
	}
}
