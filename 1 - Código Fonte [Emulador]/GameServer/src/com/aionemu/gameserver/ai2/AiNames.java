package com.aionemu.gameserver.ai2;


public enum AiNames {

	GENERAL_NPC("general"),
	DUMMY_NPC("dummy"),
	AGGRESSIVE_NPC("aggressive");

	private final String name;

	private AiNames(String name) {
		this.name = name;
	}

	public String getName() {
		return name;
	}

}
