package com.aionemu.loginserver.network.aion.serverpackets;

import java.util.Collection;
import java.util.Map;

import com.aionemu.loginserver.GameServerInfo;
import com.aionemu.loginserver.GameServerTable;
import com.aionemu.loginserver.controller.AccountController;
import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.LoginConnection;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_SERVER_LIST extends AionServerPacket {

	public SM_SERVER_LIST() {
		super(0x04);
	}

	@Override
	protected void writeImpl(LoginConnection con) {
		Collection<GameServerInfo> servers = GameServerTable.getGameServers();
		Map<Byte, Integer> charCountOnServer = AccountController.getGSCharacterCountsFor(con.getAccount().getId());
		int maxId = 0;

		writeC(servers.size()); // servers count
		writeC(con.getAccount().getLastServer());
		for (GameServerInfo gsi : servers) {
			if (gsi.getId() > maxId) {
				maxId = gsi.getId();
			}

			int cur = gsi.getCurrentPlayers();
			int max = gsi.getMaxPlayers();
			int loadLevel = 0; // 0 = Free (Green), 1 = Normal (Yellow), 2 = Crowded (Orange), 3 = Full (Red)

			int serverStatus;
			int serverBits = 0x00000401; // Classic (0x0400) + visible (0x0001)

			if (!gsi.isOnline()) {
				serverStatus = 0; // Offline -> gray
				loadLevel = 0;
			} else {
				serverStatus = 1; // Online
				if (max > 0 && cur >= max) {
					loadLevel = 3; // Full (Red)
				} else if (max > 0 && cur >= (int) (max * 0.9)) {
					loadLevel = 2; // Crowded (Orange)
				} else if (max > 0 && cur >= (int) (max * 0.7)) {
					loadLevel = 1; // Normal (Yellow)
				} else {
					loadLevel = 0; // Free / Smooth (Green)
				}
			}

			writeC(gsi.getId());
			writeB(gsi.getIp());
			writeD(gsi.getPort());
			writeC(0x00); // age limit
			writeC(0x01); // pvp=1
			writeH(cur);
			writeH(loadLevel); // bytes 13..14: load level enum in Game.dll (0=Green, 1=Yellow, 2=Orange, 3=Red)
			writeC(serverStatus);
			writeD(serverBits);
			writeC(0x00);
		}
		writeH(maxId + 1);
		writeC(0x01); // enable "last server" button & auto-connection
		for (byte gsId = 1; gsId <= maxId; gsId++) {
			writeC(charCountOnServer != null ? charCountOnServer.getOrDefault(gsId, 0) : 0);
		}
		writeB(new byte[15]); // classic na 15 bytes
	}
}
