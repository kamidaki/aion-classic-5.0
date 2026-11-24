package com.aionemu.gameserver.model.account;

public enum SielEnergyType {

	NONE(1),
	TRIAL(2),
	MEMBERSHIP(3);

	private final int id;

	private SielEnergyType(int id) {
		this.id = id;
	}

	public int getId() {
		return id;
	}

	public static SielEnergyType getSielTypeById(int id) {
		for (SielEnergyType type : values()) {
			if (type.id == id) {
				return type;
			}
		}
		return NONE;
	}
}
