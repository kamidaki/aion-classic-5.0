package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_DELETE_CHARACTER;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.services.player.PlayerService;

/**
 * In this packets aion client is requesting deletion of character.
 * 
 */
public class CM_DELETE_CHARACTER extends AionClientPacket {

	/**
	 * PlayOk2 - we dont care...
	 */
	@SuppressWarnings("unused")
	private int playOk2;
	/**
	 * ObjectId of character that should be deleted.
	 */
	private int chaOid;

	/**
	 * Constructs new instance of <tt>CM_DELETE_CHARACTER </tt> packet
	 * 
	 * @param opcode
	 */
	public CM_DELETE_CHARACTER(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void readImpl() {
		playOk2 = readD();
		chaOid = readD();
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void runImpl() {
		AionConnection client = getConnection();
		PlayerAccountData playerAccData = client.getAccount().getPlayerAccountData(chaOid);
		if (playerAccData != null && !playerAccData.isLegionMember()) {
			PlayerService.deletePlayer(playerAccData);
			client.sendPacket(new S_DELETE_CHARACTER(chaOid, playerAccData.getDeletionTimeInSeconds()));
		}
		else {
			client.sendPacket(S_MESSAGE_CODE.STR_GUILD_DISPERSE_STAYMODE_CANCEL_1);
		}
	}
}
