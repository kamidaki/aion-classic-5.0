package com.aionemu.gameserver.ai;

/**
 * @author Lost Academy Team & Durak
 */
public enum AttackIntention {
	FINISH_ATTACK,
	SIMPLE_ATTACK,
	SKILL_ATTACK,
	/** Fica em combate com o alvo e o aggro, sem atacar (Watching Eye das torres de Tiamaranta: o oficial não bate nem anda). */
	HOLD_AGGRO
}
