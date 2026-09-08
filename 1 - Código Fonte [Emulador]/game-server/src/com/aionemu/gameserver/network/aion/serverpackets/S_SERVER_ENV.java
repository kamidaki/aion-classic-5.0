package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.configs.main.GSConfig;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_SERVER_ENV extends AionServerPacket {

    @Override
    protected void writeImpl(AionConnection con) {
        writeH(350);
        writeH(2561);
        writeH(2561);
        writeH(1285);
        writeC(0x02);
        writeC(0x00);
        writeC(GSConfig.CHARACTER_REENTRY_TIME);
        writeC(0);
        writeD(0); // BOOST EVENT ID
        writeD(0); // BOOST EVENT VALUE
        writeC(1);
        writeD(0x3A);
        writeD(0x3A);
        writeD(0);
        writeD(0x64);
    }
}
