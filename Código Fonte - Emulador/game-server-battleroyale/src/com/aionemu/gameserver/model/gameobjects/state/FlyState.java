package com.aionemu.gameserver.model.gameobjects.state;

/**
 * @author Lost Academy Team & Durak
 */
public enum FlyState {

	NONE(0),
	FLYING(1),
	GLIDING(1 << 1);

	private int id;

	private FlyState(int id) {
		this.id = id;
	}

	/**
	 * @return the id
	 */
	public int getId() {
		return id;
	}
}
