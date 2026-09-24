package com.aionemu.loginserver.network.gameserver.serverpackets;

import com.aionemu.loginserver.GameServerTable;
import com.aionemu.loginserver.network.gameserver.GsAuthResponse;
import com.aionemu.loginserver.network.gameserver.GsConnection;
import com.aionemu.loginserver.network.gameserver.GsServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_GS_AUTH_RESPONSE extends GsServerPacket {

	/**
	 * Response for Gameserver authentication
	 */
	private final GsAuthResponse response;

	/**
	 * Constructor.
	 * 
	 * @param response
	 */
	public SM_GS_AUTH_RESPONSE(GsAuthResponse response) {
		this.response = response;
	}

	@Override
	protected void writeImpl(GsConnection con) {
		writeC(0);
		writeC(response.getResponseId());
		if (response == GsAuthResponse.AUTHED)
			writeC(GameServerTable.size());
	}
}
