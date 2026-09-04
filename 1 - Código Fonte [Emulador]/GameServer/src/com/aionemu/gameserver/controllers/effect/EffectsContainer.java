package com.aionemu.gameserver.controllers.effect;


public class EffectsContainer {
	
	private int skillId;
	private int skillLvl;
	private int noRemoveType;
	
	
	public EffectsContainer(int skillId, int skillLvl, int noRemoveType) {
		this.skillId = skillId;
		this.skillLvl = skillLvl;
		this.noRemoveType = noRemoveType;
	}


	public int getSkillId() {
		return skillId;
	}


	public int getSkillLvl() {
		return skillLvl;
	}


	public int getNoRemoveType() {
		return noRemoveType;
	}

}
