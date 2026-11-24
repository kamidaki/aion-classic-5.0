package com.aionemu.gameserver.skillengine.effect;

/**
 * Combinações das 3 notas de Blending da Luminess mapeadas para as habilidades finalizadoras oficiais (9000..9008).
 *
 * @author Antigravity
 */
public enum BlendingCombo {
	AAA(9000),
	AAB(9001),
	AAC(9002),
	BBB(9003),
	BBA(9004),
	BBC(9005),
	CCC(9006),
	CCA(9007),
	CCB(9008),
	DO(9022);

	private final int skillId;

	BlendingCombo(int skillId) {
		this.skillId = skillId;
	}

	public int getSkillId() {
		return skillId;
	}
}
