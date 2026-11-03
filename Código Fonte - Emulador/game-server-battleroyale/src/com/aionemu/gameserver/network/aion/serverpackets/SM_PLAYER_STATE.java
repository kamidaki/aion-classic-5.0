package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.state.CreatureVisualState;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_PLAYER_STATE extends AionServerPacket {

	private int playerObjId;
	private int visualState;
	private int seeState;

	public SM_PLAYER_STATE(Creature creature) {
		this.playerObjId = creature.getObjectId();
		this.visualState = creature.getVisualState();
		this.seeState = creature.getSeeState();
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjId);
		writeC(visualState);
		writeC(seeState);
		writeC(visualState == CreatureVisualState.BLINKING.getId() ? 0x01 : 0x00);
	}
}
