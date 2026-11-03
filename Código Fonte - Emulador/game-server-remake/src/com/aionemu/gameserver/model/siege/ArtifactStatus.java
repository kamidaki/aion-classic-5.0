package com.aionemu.gameserver.model.siege;

/**
 * @author Lost Academy Team & Durak
 */
public enum ArtifactStatus {
	IDLE(0),
	ACTIVATION(1),
	CASTING(2),
	ACTIVATED(3);

	private int id;

	ArtifactStatus(int id) {
		this.id = id;
	}

	public int getValue() {
		return id;
	}
}
