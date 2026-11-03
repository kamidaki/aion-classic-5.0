package com.aionemu.gameserver.skillengine.properties;

import com.aionemu.gameserver.skillengine.model.SkillTemplate;

/**
 * target_race_restriction do cliente 5.0: tira da lista quem não é de uma das raças que a skill aceita. Sem a marca (o caso de todas as skills
 * menos as 8 do Moreth), a lista passa inteira.
 */
public class TargetRaceProperty {

	public static boolean set(Properties.ValidationResult result, SkillTemplate skillTemplate) {
		if (skillTemplate == null || skillTemplate.getTargetRaces().isEmpty())
			return true;
		result.getTargets().removeIf(effected -> !skillTemplate.canTargetRace(effected));
		return true;
	}
}
