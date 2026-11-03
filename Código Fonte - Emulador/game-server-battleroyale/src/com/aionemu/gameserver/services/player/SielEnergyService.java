package com.aionemu.gameserver.services.player;

import java.sql.Timestamp;

import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.AccountSielEnergy;
import com.aionemu.gameserver.model.account.SielEnergyType;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.S_GAMEPASS_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_GAMEPASS_OTHER_UPDATED;
import com.aionemu.gameserver.utils.PacketSendUtility;

public class SielEnergyService {

	public void onLogout(Player player) {
		if (player == null) {
			return;
		}
		Account account = player.getAccount();
		if (account != null && account.getAccountSielEnergy() != null) {
			account.getAccountSielEnergy().end(player);
		}
	}

	public void onLogin(Player player) {
		if (player == null) {
			return;
		}
		Account account = player.getAccount();
		if (account != null) {
			if (account.getAccountSielEnergy() == null) {
				Timestamp end = new Timestamp(System.currentTimeMillis() + 365L * 24 * 3600 * 1000);
				account.setAccountSielEnergy(new AccountSielEnergy(SielEnergyType.MEMBERSHIP, new Timestamp(System.currentTimeMillis()), end, 3600));
			}
			account.getAccountSielEnergy().apply(player);
			PacketSendUtility.broadcastPacket(player, new S_GAMEPASS_OTHER_UPDATED(player.getObjectId(), account.getAccountSielEnergy().getType()));
			PacketSendUtility.sendPacket(player, new S_GAMEPASS_INFO(account.getAccountSielEnergy()));

		}
	}

	public void onUpdate(final Player player, final AccountSielEnergy old, final AccountSielEnergy accountSielEnergy) {
		if (player == null || accountSielEnergy == null) {
			return;
		}
		PacketSendUtility.broadcastPacketAndReceive(player, new S_GAMEPASS_OTHER_UPDATED(player.getObjectId(), accountSielEnergy.getType()));
		PacketSendUtility.sendPacket(player, new S_GAMEPASS_INFO(accountSielEnergy));

		if (old != null && old.getType() != SielEnergyType.NONE) {
			old.end(player);
		}

		accountSielEnergy.apply(player);
	}

	public static SielEnergyService getInstance() {
		return SingletonHolder.instance;
	}

	private static class SingletonHolder {
		protected static final SielEnergyService instance = new SielEnergyService();
	}
}
