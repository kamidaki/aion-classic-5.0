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
        writeH(2570);
        writeC(0x02);
        writeC(0x00);
        writeC(GSConfig.CHARACTER_REENTRY_TIME);
        writeC(0);
        writeD(0); // BOOST EVENT ID
        writeD(100); // BOOST EVENT VALUE
        writeC(1);
        writeD(0x4B);
        writeD(0x4B);
        writeD(0);
        writeD(0x64);
        // The official 5.0 environment payload is 60 bytes, including these feature fields.
        // A truncated environment leaves newer client interfaces without their configuration.
        writeB(new byte[2]); // 37..38
        writeD(60); // 39
        writeC(2); // 43
        writeD(60); // 44
        writeH(0x7FFF); // 48
        writeH(0); // 50
        writeD((int) (System.currentTimeMillis() / 1000)); // 52
        writeD(0); // 56
    }
}
