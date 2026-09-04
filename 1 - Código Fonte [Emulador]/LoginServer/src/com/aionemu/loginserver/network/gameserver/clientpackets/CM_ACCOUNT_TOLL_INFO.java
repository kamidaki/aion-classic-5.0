package com.aionemu.loginserver.network.gameserver.clientpackets;

import com.aionemu.loginserver.dao.AccountDAO;
import com.aionemu.loginserver.dao.PremiumDAO;
import com.aionemu.loginserver.model.Account;
import com.aionemu.loginserver.network.gameserver.GsClientPacket;


public class CM_ACCOUNT_TOLL_INFO extends GsClientPacket {

	private long toll;
	private long luna;

	private String accountName;

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void readImpl() {
		toll = readQ();
		accountName = readS();
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void runImpl() {
		Account account =AccountDAO.getAccount(accountName);

		if (account != null) {
			PremiumDAO.updateToll(account.getId(), toll, 0);
		}
	}
}
