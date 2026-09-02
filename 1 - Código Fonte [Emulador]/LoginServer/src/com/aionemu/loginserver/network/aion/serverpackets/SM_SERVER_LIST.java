package com.aionemu.loginserver.network.aion.serverpackets;

import java.util.Collection;
import java.util.Map;

import com.aionemu.loginserver.GameServerInfo;
import com.aionemu.loginserver.GameServerTable;
import com.aionemu.loginserver.controller.AccountController;
import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.LoginConnection;

public class SM_SERVER_LIST extends AionServerPacket {
	public SM_SERVER_LIST() {
		super(0x04);
	}

	@Override
	protected void writeImpl(LoginConnection con) {
		Collection<GameServerInfo> servers = GameServerTable.getGameServers();
		Map<Integer, Integer> charactersCountOnServer = null;

		int accountId = con.getAccount().getId();
		int maxId = 0;

		charactersCountOnServer = AccountController.getGSCharacterCountsFor(accountId);
		writeC(getOpcode());
		writeC(servers.size());// servers
		writeC(con.getAccount().getLastServer());// last server
		for (GameServerInfo gsi : servers) {
			if (gsi.getId() > maxId)
				maxId = gsi.getId();

			writeC(gsi.getId());// server id
			writeB(gsi.getIPAddressForPlayer(con.getIP())); // server IP
			writeD(gsi.getPort());// port
			writeC(0x00); // age limit
			writeC(0x01);// pvp=1
			writeH(gsi.getCurrentPlayers());// currentPlayers
			writeH(gsi.getMaxPlayers());// maxPlayers

			int serverStatus;
			int serverBits;

			if (!gsi.isOnline()) {
				// Offline / Desligado (Bolinha Cinza)
				serverStatus = 0;
				serverBits = 0x00000401; // Classic (0x0400) + Bit 0 (0x0001)
			} else if (gsi.isMaintenance()) {
				// Manutenção (Bloqueio para jogadores comuns)
				serverStatus = 2; // Código canônico de manutenção no protocolo Aion
				serverBits = 0x00000401; // Classic + Bit 0
			} else if (gsi.isFull()) {
				// Lotado / Full (Bolinha Vermelha)
				serverStatus = 1;
				serverBits = 0x00000401; // Classic + Bit 0
			} else {
				// Online / Livre (Bolinha Verde)
				serverStatus = 1;
				serverBits = 0x00000401; // Classic (0x0400) + Bit 0 (0x0001)
			}

			writeC(serverStatus);
			writeD(serverBits);
			writeC(0x00);
		}

		writeH(maxId + 1);
		writeC(0x01);

		for (int i = 1; i <= maxId; i++) {
			if (charactersCountOnServer.containsKey(i))
				writeC(charactersCountOnServer.get(i));
			else
				writeC(0);
		}
		writeB(new byte[15]); // classic na 15 bytes
	}
}