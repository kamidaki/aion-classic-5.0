package com.aionemu.gameserver.skillengine.effect;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

/**
 * Resolvedor determinístico de combos de Blending.
 *
 * @author Antigravity
 */
public final class BlendingResolver {

	private static final Map<String, Integer> COMBOS = new HashMap<>();

	static {
		for (BlendingCombo combo : BlendingCombo.values()) {
			COMBOS.put(combo.name(), combo.getSkillId());
		}
	}

	private BlendingResolver() {
	}

	public static Integer resolve(Collection<BlendingNote> notes) {
		if (notes == null || notes.size() != 3) {
			return null;
		}
		StringBuilder sb = new StringBuilder(3);
		for (BlendingNote note : notes) {
			if (note == null) {
				return null;
			}
			sb.append(note.name());
		}
		return COMBOS.get(sb.toString());
	}
}
