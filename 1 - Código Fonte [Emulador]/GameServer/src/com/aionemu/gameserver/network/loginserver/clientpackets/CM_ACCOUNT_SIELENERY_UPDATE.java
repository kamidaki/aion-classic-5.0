package com.aionemu.gameserver.network.loginserver.clientpackets;

import com.aionemu.gameserver.model.account.AccountSielEnergy;
import com.aionemu.gameserver.model.account.SielEnergyType;
import com.aionemu.gameserver.network.loginserver.LoginServer;
import com.aionemu.gameserver.network.loginserver.LsClientPacket;

import java.sql.Timestamp;


public class CM_ACCOUNT_SIELENERY_UPDATE extends LsClientPacket {


    private int accountId;
    private int type;
    private long chargeTime;
    private long end;
    private long remain;

    public CM_ACCOUNT_SIELENERY_UPDATE(int opCode) {
        super(opCode);
    }


    /**
     * {@inheritDoc}
     */
    @Override
    public void readImpl() {
        accountId = readD();
        type = readD();
        chargeTime = readQ();
        end = readQ();
        remain = readQ();
    }


    /**
     * {@inheritDoc}
     */
    @Override
    public void runImpl() {
        final AccountSielEnergy accountSielEnergy = new AccountSielEnergy(SielEnergyType.getSielTypeById(type), new Timestamp(chargeTime), end == 0 ? null : new Timestamp(end), remain);
        LoginServer.getInstance().updateAccountSielEnergy(accountId, accountSielEnergy);
    }
}
