package com.aionemu.gameserver.network.aion.iteminfo;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemStone;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Set;

public class ManaStoneInfoBlobEntry extends ItemBlobEntry {
    ManaStoneInfoBlobEntry() {
        super(ItemBlobType.MANA_SOCKETS);
    }

    @Override
    public void writeThisBlob(ByteBuffer buf) {
        Item item = ownerItem;
        writeC(buf, item.isSoulBound() ? 1 : 0);
        writeC(buf, item.getEnchantLevel());
        writeD(buf, item.getItemSkinTemplate().getTemplateId());
        writeC(buf, item.getOptionalSocket());

        writeItemStones(buf);
        ItemStone god = item.getGodStone();
        writeD(buf, god == null ? 0 : god.getItemId());

        int itemColor = item.getItemColor();
        int dyeExpiration = item.getColorTimeLeft();
        if ((dyeExpiration > 0 && item.getColorExpireTime() > 0 || dyeExpiration == 0 && item.getColorExpireTime() == 0) && item.getItemTemplate().isItemDyePermitted()) {
            writeC(buf, itemColor == 0 ? 0 : 1);
            writeD(buf, itemColor);
            writeD(buf, 0); // unk 1.5.1.9
            writeD(buf, dyeExpiration); // seconds until dye expires
        } else {
			writeC(buf, itemColor == 0 ? 0 : 1);
			writeD(buf, itemColor);
            writeD(buf, 0); // unk 1.5.1.9
            writeD(buf, 0);
        }

        writeD(buf, 0);//2.4
        writeD(buf, 0);//2.4
        writeD(buf, 0);//2.8

        writeTail50(buf);
    }

    /**
     * 5.0 Classic: a entrada tem 441 bytes, nao 60. O corpo acima cobre os 60
     * primeiros - e os bytes 2..5 dele ja sao o id do item, como na captura. O
     * restante e zero, exceto dez bytes constantes nas tres amostras oficiais
     * do 01_Login_World (arma, torso e calca).
     */
    private static final int BODY_SIZE = 60;
    private static final int TOTAL_SIZE = 441;

    private void writeTail50(ByteBuffer buf) {
        byte[] tail = new byte[TOTAL_SIZE - BODY_SIZE];
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
        int count = 0;

        if (item.hasManaStones()) {
            Set<ManaStone> itemStones = item.getItemStones();

            for (ManaStone itemStone : itemStones) {
                if (count == 6)
                    break;

                StatFunction modifier = itemStone.getFirstModifier();
                if (modifier != null) {
                    count++;
                    writeH(buf, modifier.getName().getItemStoneMask());
                }
            }
            skip(buf, (6 - count) * 2);
            count = 0;
            for (ManaStone itemStone : itemStones) {
                if (count == 6)
                    break;

                StatFunction modifier = itemStone.getFirstModifier();
                if (modifier != null) {
                    count++;
                    writeH(buf, modifier.getValue());
                }
            }
            skip(buf, (6 - count) * 2);
        } else {
            skip(buf, 24);
        }
        // for now max 6 stones - write some junk
    }

    @Override
    public int getSize() {
        return TOTAL_SIZE;
    }
}