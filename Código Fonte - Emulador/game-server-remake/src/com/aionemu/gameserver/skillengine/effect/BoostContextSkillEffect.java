package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;

/**
 * Buff que troca skills pelas versões de contexto do client_context_skill_info (FeverCondition: as _high do Brawler). O cliente faz a troca ao ver o
 * ícone no 0x31; o servidor só usa o buff para aceitar a skill de contexto ({@link com.aionemu.gameserver.skillengine.condition.ContextSkillCondition}).
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BoostContextSkillEffect")
public class BoostContextSkillEffect extends BufEffect {

	@XmlAttribute(required = true)
	protected String condition;

	@Override
	public void calculate(Effect effect) {
		effect.addSuccessEffect(this);
	}

	public String getCondition() {
		return condition;
	}

	/**
	 * @return True, se o efeito vem de uma skill com BoostContextSkill da condição dada
	 */
	public static boolean grants(Effect effect, String condition) {
		SkillTemplate template = effect.getSkillTemplate();
		if (template.getEffects() == null)
			return false;
		for (EffectTemplate effectTemplate : template.getEffects().getEffects()) {
			if (effectTemplate instanceof BoostContextSkillEffect boost && boost.condition.equalsIgnoreCase(condition))
				return true;
		}
		return false;
	}
}
