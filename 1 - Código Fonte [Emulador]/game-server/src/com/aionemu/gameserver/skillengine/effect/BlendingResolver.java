package com.aionemu.gameserver.skillengine.effect;

import java.util.Collection;

/**
 * Resolvedor determinístico de combos de Blending.
 *
 * Verificado na captura oficial do Classic 5.0:
 * A ordem das notas não importa (multiset):
 * - 3x A -> 9000 (AAA)
 * - 2x A + 1x B -> 9001 (AAB)
 * - 2x A + 1x C -> 9002 (AAC)
 * - 3x B -> 9003 (BBB)
 * - 2x B + 1x A -> 9004 (BBA)
 * - 2x B + 1x C -> 9005 (BBC)
 * - 3x C -> 9006 (CCC)
 * - 2x C + 1x A -> 9007 (CCA)
 * - 2x C + 1x B -> 9008 (CCB)
 *
 * @author Antigravity
 */
public final class BlendingResolver {

	private BlendingResolver() {
	}

	public static Integer resolve(Collection<BlendingNote> notes) {
		if (notes == null || notes.size() != 3) {
			return null;
		}
		int a = 0, b = 0, c = 0;
		for (BlendingNote note : notes) {
			if (note == null) {
				return null;
			}
			switch (note) {
				case A -> a++;
				case B -> b++;
				case C -> c++;
				default -> {}
			}
		}
		if (a == 3) return BlendingCombo.AAA.getSkillId();
		if (a == 2 && b == 1) return BlendingCombo.AAB.getSkillId();
		if (a == 2 && c == 1) return BlendingCombo.AAC.getSkillId();
		if (b == 3) return BlendingCombo.BBB.getSkillId();
		if (b == 2 && a == 1) return BlendingCombo.BBA.getSkillId();
		if (b == 2 && c == 1) return BlendingCombo.BBC.getSkillId();
		if (c == 3) return BlendingCombo.CCC.getSkillId();
		if (c == 2 && a == 1) return BlendingCombo.CCA.getSkillId();
		if (c == 2 && b == 1) return BlendingCombo.CCB.getSkillId();
		return null;
	}
}
