package com.aionemu.gameserver.model.gameobjects.player.motion;

import com.aionemu.gameserver.model.Expirable;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class Motion implements Expirable {

	/**
	 * Slot of each custom animation, indexed by motion id, from the client's animations/custom_animation.xml (Classic 5.0, ids 1-105).
	 * The slots follow the client's motion tab and the 7 ids of SM_MOTION action 7: 1 idle, 2 run, 3 jump, 4 rest, 5 shop, 6 provoc, 7 away.
	 */
	private static final byte[] TYPES = {
		0, 1, 2, 3, 4, 1, 2, 3, 4, 1, 1, 1, 1, 2, 3, 4, 1, 2, 3, 4, 5, 1, 1, 1, 1,
		3, 4, 4, 4, 1, 2, 3, 4, 4, 5, 1, 1, 4, 1, 1, 1, 4, 1, 1, 5, 1, 1, 2, 3, 4,
		4, 1, 2, 3, 4, 5, 4, 5, 1, 1, 2, 3, 2, 3, 1, 1, 1, 2, 3, 4, 1, 2, 3, 4, 1,
		1, 2, 3, 4, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 1, 2, 3, 4, 1, 2, 3,
		4, 4, 1, 2, 3, 4,
	};

	/**
	 * @return the slot (1 idle ... 5 shop) of the motion, or 0 for an id the client doesn't know
	 */
	public static int getType(int motionId) {
		return motionId > 0 && motionId < TYPES.length ? TYPES[motionId] : 0;
	}

	private int id;
	private int deletionTime = 0;
	private boolean active = false;

	/**
	 * @param id
	 * @param deletionTime
	 */
	public Motion(int id, int deletionTime, boolean isActive) {
		this.id = id;
		this.deletionTime = deletionTime;
		this.active = isActive;
	}

	/**
	 * @return the id
	 */
	public int getId() {
		return id;
	}

	/**
	 * @return the active
	 */
	public boolean isActive() {
		return active;
	}

	/**
	 * @param active
	 *          the active to set
	 */
	public void setActive(boolean active) {
		this.active = active;
	}

	@Override
	public int getExpireTime() {
		return deletionTime;
	}

	@Override
	public void onExpire(Player player) {
		player.getMotions().onExpire(this);
		// TODO motion templates -> parse nameIds for system message, like 600533 for STR_CMOTION_CASH_NINJA_IDLE (Ninja Idle) etc.
		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_DELETE_CASH_CUSTOMANIMATION_BY_TIMEOUT(/* nameId */));
	}

}
