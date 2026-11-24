package com.aionemu.gameserver.skillengine.effect;

/**
 * Notas musicais da mecânica de Blending da classe Luminess (A = Lu, B = La, C = Fe).
 *
 * @author Antigravity
 */
public enum BlendingNote {
	A,
	B,
	C,
	E,
	SEAL;

	public static BlendingNote fromString(String value) {
		if (value == null || value.isEmpty()) {
			return null;
		}
		try {
			return valueOf(value.trim().toUpperCase());
		} catch (IllegalArgumentException e) {
			return null;
		}
	}
}
