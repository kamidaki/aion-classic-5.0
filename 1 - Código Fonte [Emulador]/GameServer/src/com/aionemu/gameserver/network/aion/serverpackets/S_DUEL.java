package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.model.DuelResult;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_DUEL extends AionServerPacket {

	private String playerName;
	private DuelResult result;
	private int requesterObjId;
	private int type;

	private S_DUEL(int type) {
		this.type = type;
	}

	public static S_DUEL SM_DUEL_STARTED(int requesterObjId) {
		S_DUEL packet = new S_DUEL(0x00);
		packet.setRequesterObjId(requesterObjId);
		return packet;
	}

	private void setRequesterObjId(int requesterObjId) {
		this.requesterObjId = requesterObjId;
	}

	public static S_DUEL SM_DUEL_RESULT(DuelResult result, String playerName) {
		S_DUEL packet = new S_DUEL(0x01);
		packet.setPlayerName(playerName);
		packet.setResult(result);
		return packet;
	}

	private void setPlayerName(String playerName) {
		this.playerName = playerName;
	}

	private void setResult(DuelResult result) {
		this.result = result;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(type);

		switch (type) {
			case 0x00:
				writeD(requesterObjId);
				break;
			case 0x01:
				writeC(result.getResultId()); // unknown
				writeD(result.getMsgId());
				writeS(playerName);
				break;
			case 0xE0:
				break;
			default:
				throw new IllegalArgumentException("invalid SM_DUEL packet type " + type);
		}
	}
}
