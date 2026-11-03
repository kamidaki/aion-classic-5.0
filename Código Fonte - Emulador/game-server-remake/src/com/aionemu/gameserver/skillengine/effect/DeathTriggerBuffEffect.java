package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Soul Pact (RB_SoulRemnant_G1/G2): enquanto o buff dura, o golpe que zeraria o HP não mata. O buff sai, o HP vai a {@code value}% do máximo e
 * entra a skill {@code skill_id}, o Soul Rest ({@link DeathTrialStateEffect}).
 * <p>
 * client_skills 5.0: DeathTriggerBuff, reserved1 = skill do Soul Rest, reserved3 = % do HP máximo (100 no G1, 150 no G2). O HP do servidor não
 * passa do máximo, então o G2 também volta com 100%.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "DeathTriggerBuffEffect")
public class DeathTriggerBuffEffect extends EffectTemplate {

	@XmlAttribute(name = "skill_id", required = true)
	protected int skillId;

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}

	@Override
	public void calculate(Effect effect) {
		effect.addSuccessEffect(this);
	}

	/**
	 * @return A Soul Pact ativa no jogador, ou null
	 */
	public static Effect findActive(Player player) {
		for (Effect effect : player.getEffectController().getAbnormalEffects()) {
			if (effect.getSkillTemplate().hasAnyEffect(EffectType.DEATHTRIGGERBUFF))
				return effect;
		}
		return null;
	}

	/**
	 * Chamado uma vez por Soul Pact, depois que o golpe fatal deixou o jogador com 1 de HP.
	 */
	public static void trigger(Player player, Effect effect) {
		for (EffectTemplate template : effect.getEffectTemplates()) {
			if (template instanceof DeathTriggerBuffEffect buff) {
				effect.endEffect();
				player.getLifeStats().setCurrentHpPercent(Math.clamp(buff.value, 1, 100));
				Effect soulRest = SkillEngine.getInstance().applyEffectDirectly(buff.skillId, player, player);
				if (soulRest != null)
					PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_SKILL_SUCC_DeathTrialState_ME_TO_SELF(soulRest.getSkillTemplate().getL10n()));
				return;
			}
		}
	}
}
