package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_USER_CLASSIC_WARDROBE_LOAD extends AionServerPacket {

    private final Player player;

    public S_USER_CLASSIC_WARDROBE_LOAD(Player player) {
        this.player = player;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(this.player.getCommonData().getWardrobeSlot());
        writeH(this.player.getPlayerWardrobe().size());
        for (WardrobeEntry wardrobeEntry : this.player.getPlayerWardrobe().values()){
            writeD(wardrobeEntry.getObjectId());
            writeD(wardrobeEntry.getItemId());
            writeD(wardrobeEntry.getColor());
            writeC(wardrobeEntry.isLiked() ? 1 : 0);
        }
        /*
         * A captura oficial fecha em 7 bytes com o guarda-roupa vazio (`01 00 00 00 00 00 01`);
         * sem este byte final o nosso fecha em 6. O valor observado e 1; o significado do campo
         * ainda e desconhecido.
         */
        writeC(0x01);
    }
}
