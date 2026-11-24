package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_POSITION extends AionServerPacket {

	private final VisibleObject object;

	public SM_POSITION(VisibleObject object) {
		this.object = object;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(object.getObjectId());
		writeF(object.getX());
		writeF(object.getY());
		writeF(object.getZ());
		writeC(object.getHeading());
	}
}
