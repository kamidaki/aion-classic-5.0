package com.aionemu.gameserver.skillengine.condition;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.effect.BoostContextSkillEffect;
import com.aionemu.gameserver.skillengine.model.Skill;

/**
 * Skill de contexto (client_context_skill_info): só pode ser usada enquanto o jogador tem o buff que a libera, por exemplo as _high do Brawler durante
 * o Fever (FeverCondition).
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ContextSkillCondition")
public class ContextSkillCondition extends Condition {

	@XmlAttribute(required = true)
	protected String condition;

	@Override
	public boolean validate(Skill skill) {
		return canValidate(skill);
	}

	@Override
	public boolean canValidate(Skill skill) {
		// 5.0 oficial: ST_myung_high_G6 fora do Fever foi descartada em silêncio, sem S_USE_SKILL, cancelamento nem mensagem
		if (!(skill.getEffector() instanceof Player player))
			return true;
		return player.getEffectController().hasAbnormalEffect(effect -> BoostContextSkillEffect.grants(effect, condition));
	}
}
