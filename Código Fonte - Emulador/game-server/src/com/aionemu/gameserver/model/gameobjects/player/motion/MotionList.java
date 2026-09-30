package com.aionemu.gameserver.model.gameobjects.player.motion;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

import com.aionemu.gameserver.dao.MotionDAO;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MOTION;
import com.aionemu.gameserver.taskmanager.tasks.ExpireTimerTask;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class MotionList {

	private Player owner;
	private Map<Integer, Motion> activeMotions;
	private Map<Integer, Motion> motions;

	/**
	 * @param owner
	 */
	public MotionList(Player owner) {
		this.owner = owner;
	}

	/**
	 * @return the activeMotions
	 */
	public Map<Integer, Motion> getActiveMotions() {
		if (activeMotions == null)
			return Collections.emptyMap();
		return activeMotions;
	}

	/**
	 * @return the motions
	 */
	public Map<Integer, Motion> getMotions() {
		if (motions == null)
			return Collections.emptyMap();
		return motions;
	}

	/**
	 * Adds a motion; an active one takes its slot. Getting a motion the player already owns replaces it (new expiration), except that a
	 * permanent motion is never replaced by a timed one.
	 *
	 * @return false if the player keeps the motion he already had
	 */
	public boolean add(Motion motion, boolean persist) {
		if (motions == null)
			motions = new LinkedHashMap<>();
		Motion owned = motions.get(motion.getId());
		if (owned != null) {
			if (owned.getExpireTime() == 0 && motion.getExpireTime() != 0)
				return false;
			if (persist) {
				motion.setActive(motion.isActive() || owned.isActive());
				remove(owned.getId(), false);
			}
		}
		motions.put(motion.getId(), motion);
		int type = Motion.getType(motion.getId());
		if (type == 0)
			motion.setActive(false);
		if (motion.isActive()) {
			if (activeMotions == null)
				activeMotions = new LinkedHashMap<>();
			Motion old = activeMotions.put(type, motion);
			if (old != null && old != motion) {
				old.setActive(false);
				if (persist)
					MotionDAO.updateMotion(owner.getObjectId(), old);
			}
		}
		if (persist) {
			if (motion.getExpireTime() != 0)
				ExpireTimerTask.getInstance().registerExpirable(motion, owner);
			MotionDAO.storeMotion(owner.getObjectId(), motion);
		}
		return true;
	}

	/**
	 * Removes the motion (expiration). Only the instance still in the list goes away: a motion replaced by {@link #add} keeps its old
	 * instance in the expire task.
	 */
	public void onExpire(Motion motion) {
		if (motions != null && motions.get(motion.getId()) == motion && remove(motion.getId(), true))
			PacketSendUtility.broadcastPacket(owner, new SM_MOTION(owner.getObjectId(), activeMotions), true);
	}

	public boolean remove(int motionId) {
		return remove(motionId, true);
	}

	/**
	 * @return true if the motion was active
	 */
	private boolean remove(int motionId, boolean notify) {
		Motion motion = motions == null ? null : motions.remove(motionId);
		if (motion == null)
			return false;
		if (notify)
			PacketSendUtility.sendPacket(owner, new SM_MOTION((short) motionId));
		MotionDAO.deleteMotion(owner.getObjectId(), motionId);
		if (motion.isActive() && activeMotions != null)
			return activeMotions.remove(Motion.getType(motionId), motion);
		return false;
	}

	/**
	 * Motion tab: motion id 0 clears the slot. As in the official capture motion.pcapng, the server answers with the look of the player
	 * (action 7, to everyone around) and then confirms the change to him (action 5).
	 */
	public void setActive(int motionId, int motionType) {
		if (motionId != 0) {
			Motion motion = motions == null ? null : motions.get(motionId);
			if (motion == null || motion.isExpired() || Motion.getType(motionId) != motionType)
				return;
			if (activeMotions == null)
				activeMotions = new LinkedHashMap<>();
			Motion old = activeMotions.put(motionType, motion);
			if (old != null && old != motion) {
				old.setActive(false);
				MotionDAO.updateMotion(owner.getObjectId(), old);
			}
			if (!motion.isActive()) {
				motion.setActive(true);
				MotionDAO.updateMotion(owner.getObjectId(), motion);
			}
		} else {
			Motion old = activeMotions == null ? null : activeMotions.remove(motionType);
			if (old != null) {
				old.setActive(false);
				MotionDAO.updateMotion(owner.getObjectId(), old);
			}
		}
		PacketSendUtility.broadcastPacket(owner, new SM_MOTION(owner.getObjectId(), activeMotions), true);
		PacketSendUtility.sendPacket(owner, new SM_MOTION((short) motionId, (byte) motionType));
	}
}
