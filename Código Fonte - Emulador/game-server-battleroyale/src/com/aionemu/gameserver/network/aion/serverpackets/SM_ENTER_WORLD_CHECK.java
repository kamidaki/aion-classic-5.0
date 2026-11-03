package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_ENTER_WORLD_CHECK extends AionServerPacket {

	private byte msg = 0x01;
	private int characterId = 0;

	public SM_ENTER_WORLD_CHECK(Msg msg) {
		this.msg = msg.getId();
	}

	public SM_ENTER_WORLD_CHECK(byte msg) {
		this.msg = msg;
	}

	public SM_ENTER_WORLD_CHECK(int characterId) {
		this.msg = 0x01;
		this.characterId = characterId;
	}

	public SM_ENTER_WORLD_CHECK() {
		this.msg = 0x01;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		int targetId = characterId != 0 ? characterId : (con.getActivePlayer() != null ? con.getActivePlayer().getObjectId() : 0);
		writeC(msg);
		writeC(0x00);
		writeC(0x00);
		writeC(0x00);
		writeD(0x00);
		writeD(targetId);
		writeD(0x17);
		writeD(0x00);
		writeD(0x00);
	}

	public enum Msg {
		/**
		 * indicates that enter world was successful
		 */
		OK(1),

		/**
		 * The selected character is already playing on the selected server.
		 */
		CHAR_ALREADY_ONLINE(1),

		/**
		 * The connection to the game server has failed.
		 * (this disconnects and closes the client)
		 */
		CONNECTION_ERROR(2),

		/**
		 * Characters of both factions exist on the server.
		 */
		BOTH_FACTIONS(3),

		/**
		 * You cannot connect to the game during character reservation time.
		 */
		RESERVATION_TIME(4),

		/**
		 * You have exceeded the limit of characters for an account and must delete some to be able to play again.
		 */
		TOO_MANY_CHARACTERS(5),

		/**
		 * Reconnection of the character is being prepared (max. 20s).
		 */
		REENTRY_TIME(6);

		byte id;

		Msg(int id) {
			this.id = (byte) id;
		}

		byte getId() {
			return id;
		}
	}
}
