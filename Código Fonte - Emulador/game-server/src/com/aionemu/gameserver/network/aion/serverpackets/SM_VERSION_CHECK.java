package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Calendar;

import com.aionemu.gameserver.configs.main.GSConfig;
import com.aionemu.gameserver.configs.main.MembershipConfig;
import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.chatserver.ChatServer;

public class SM_VERSION_CHECK extends AionServerPacket {

	private int version;
	private int characterLimitCount;
	private final int characterFactionsMode;
	private final int characterCreateMode;

	public SM_VERSION_CHECK(com.aionemu.gameserver.model.EventTheme eventTheme) {
		this(192);
	}

	public SM_VERSION_CHECK(int version) {
		this.version = version;
		if (MembershipConfig.CHARACTER_ADDITIONAL_ENABLE != 10 && MembershipConfig.CHARACTER_ADDITIONAL_COUNT > GSConfig.CHARACTER_LIMIT_COUNT) {
			characterLimitCount = MembershipConfig.CHARACTER_ADDITIONAL_COUNT;
		} else {
			characterLimitCount = GSConfig.CHARACTER_LIMIT_COUNT;
		}
		if (GSConfig.CHARACTER_CREATION_MODE < 0 || GSConfig.CHARACTER_CREATION_MODE > 2) {
			characterFactionsMode = 0;
		} else {
			characterFactionsMode = GSConfig.CHARACTER_CREATION_MODE;
		}
		if (GSConfig.CHARACTER_FACTION_LIMITATION_MODE < 0 || GSConfig.CHARACTER_FACTION_LIMITATION_MODE > 3) {
			characterCreateMode = 0;
		} else {
			characterCreateMode = GSConfig.CHARACTER_FACTION_LIMITATION_MODE * 0x04;
		}
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (version < 192) {
			writeC(0x02);
			return;
		}
		writeC(0x00);
		writeC(NetworkConfig.GAMESERVER_ID);
		writeD(240726);
		writeD(240726);
		writeD(0);
		writeD(240726);
		writeD((int) (Calendar.getInstance().getTimeInMillis() / 1000));
		writeC(0);
		writeC(GSConfig.SERVER_COUNTRY_CODE);
		writeC(0);
		int s = (characterLimitCount * 0x10) | characterFactionsMode;
		writeC(s | characterCreateMode);
		writeD((int) (Calendar.getInstance().getTimeInMillis() / 1000));
		writeD(-28800);
		writeD(0);
		writeH(1); // loop size
		{
			writeC(0x00); // spacer
			byte[] chatIp = ChatServer.getInstance().getPublicIP();
			if (chatIp == null || chatIp.length == 0) {
				if (NetworkConfig.CLIENT_CONNECT_ADDRESS != null && NetworkConfig.CLIENT_CONNECT_ADDRESS.getAddress() != null) {
					chatIp = NetworkConfig.CLIENT_CONNECT_ADDRESS.getAddress().getAddress();
				} else {
					chatIp = new byte[] { 127, 0, 0, 1 };
				}
			}
			writeB(chatIp);
			int port = ChatServer.getInstance().getPublicPort();
			if (port == 0) {
				port = NetworkConfig.CHAT_ADDRESS != null ? NetworkConfig.CHAT_ADDRESS.getPort() : 9021;
			}
			writeH(port);
		}
		writeD(0);
		writeC(0);
	}
}
