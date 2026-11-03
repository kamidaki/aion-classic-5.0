package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.controllers.movement.MovementMask;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.network.aion.AionConnection;

public class S_MOVE_NEW extends SM_MOVE {

	private final int objectId;
	private final float sX, sY, sZ;
	private final float tX, tY, tZ;
	private final byte heading;
	private final byte moveTypeFlag;
	private final boolean explicitCoordinates;

	public S_MOVE_NEW(Creature creature) {
		super(creature);
		this.explicitCoordinates = false;
		this.objectId = creature.getObjectId();
		this.sX = creature.getX();
		this.sY = creature.getY();
		this.sZ = creature.getZ();
		this.tX = 0;
		this.tY = 0;
		this.tZ = 0;
		this.heading = creature.getHeading();
		this.moveTypeFlag = creature.getMoveController().getMovementMask();
	}

	public S_MOVE_NEW(int objectId, float sX, float sY, float sZ, float tX, float tY, float tZ, byte heading, byte flag) {
		super(null, flag);
		this.explicitCoordinates = true;
		this.objectId = objectId;
		this.sX = sX;
		this.sY = sY;
		this.sZ = sZ;
		this.tX = tX;
		this.tY = tY;
		this.tZ = tZ;
		this.heading = heading;
		this.moveTypeFlag = flag;
	}

	@Override
	protected void writeImpl(AionConnection client) {
		if (explicitCoordinates) {
			writeD(objectId);
			writeF(sX);
			writeF(sY);
			writeF(sZ);
			writeC(heading);
			writeC(moveTypeFlag);
			if ((moveTypeFlag & MovementMask.STARTMOVE) == MovementMask.STARTMOVE || (moveTypeFlag & MovementMask.NPC_STARTMOVE) == MovementMask.NPC_STARTMOVE) {
				writeF(tX);
				writeF(tY);
				writeF(tZ);
			}
		} else {
			super.writeImpl(client);
		}
	}
}
