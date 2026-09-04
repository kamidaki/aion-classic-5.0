package com.aionemu.gameserver.model.gameobjects.state;


public enum CreatureState
{
    ACTIVE(1),
    FLYING(2),
    FLIGHT_TELEPORT(2),
    RESTING(4),
    DEAD(7), //6 ??
    CHAIR(6),
    FLOATING_CORPSE(8),
    PRIVATE_SHOP(10),
    LOOTING(12),
    WEAPON_EQUIPPED(32),
    WALKING(64),
    NPC_IDLE(64),
    POWERSHARD(128),
    TREATMENT(256),
    GLIDING(512);


	/**
	 * Standing, path flying, free flying, riding, sitting, sitting on chair, dead, fly dead, private shop, looting, fly
	 * looting, default
	 */

	private int id;

	private CreatureState(int id) {
		this.id = id;
	}

	/**
	 * @return the id
	 */
	public int getId() {
		return id;
	}
}
