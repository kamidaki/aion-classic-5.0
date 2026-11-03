package com.aionemu.gameserver.skillengine.model;

/**
 * @author Lost Academy Team & Durak
 */
public enum DashStatus {
	NONE(0),
	RANDOMMOVELOC(1),
	DASH(2),
	BACKDASH(3),
	MOVEBEHIND(4),
	RANDOMMOVELOC_NEW(6),
	/** RandomMoveLoc com reserved5 = 2 (RB_OblivionDash): 5.0 oficial manda dash 8, heading e o destino a {@code distance} m na direção do heading */
	RANDOMMOVELOC_DASH(8);

	private int id;

	private DashStatus(int id) {
		this.id = id;
	}

	public int getId() {
		return id;
	}

}
