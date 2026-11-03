package com.aionemu.gameserver.skillengine.effect;

import java.util.concurrent.Future;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ATTACK_STATUS.LOG;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ATTACK_STATUS.TYPE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * Soul Rest (RB_SoulRemnant_G1/G2_Effect), que a Soul Pact aplica no lugar da morte: a cada {@code checktime} ms o HP cai {@code value}% do
 * máximo, e morrer nesse estado é definitivo. Dar o golpe final numa criatura encerra o estado e aplica {@code skill_id}
 * (RB_SoulRemnant_G1_Heal, cura de 100%), que é o "volta ao estado original" da descrição.
 * <p>
 * client_skills 5.0: DeathTrialState, reserved2 = % do HP máximo por tick (7), reserved3 = intervalo (1000), reserved6 = skill do fim.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "DeathTrialStateEffect")
public class DeathTrialStateEffect extends EffectTemplate {

	@XmlAttribute(required = true)
	protected int checktime;

	@XmlAttribute(name = "skill_id")
	protected int skillId;

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}

	@Override
	public void calculate(Effect effect) {
		effect.addSuccessEffect(this);
	}

	@Override
	public void startEffect(Effect effect) {
		Future<?> task = ThreadPoolManager.getInstance().scheduleAtFixedRate(() -> onPeriodicAction(effect), checktime, checktime);
		effect.setPeriodicTask(task, position);
	}

	@Override
	public void onPeriodicAction(Effect effect) {
		Creature effected = effect.getEffected();
		int damage = (int) ((long) effected.getLifeStats().getMaxHp() * value / 100);
		effected.getLifeStats().reduceHp(TYPE.DAMAGE, Math.max(1, damage), 0, LOG.REGULAR, effected);
	}

	/**
	 * Chamado quando {@code killer} dá o golpe final numa criatura: encerra o Soul Rest e aplica a skill do fim.
	 */
	public static void onKill(Player killer) {
		for (Effect effect : killer.getEffectController().getAbnormalEffects()) {
			if (!effect.getSkillTemplate().hasAnyEffect(EffectType.DEATHTRIALSTATE))
				continue;
			for (EffectTemplate template : effect.getEffectTemplates()) {
				if (template instanceof DeathTrialStateEffect state) {
					effect.endEffect();
					PacketSendUtility.sendPacket(killer, SM_SYSTEM_MESSAGE.STR_SKILL_SUCC_DeathTrialState_END_ME_TO_SELF());
					if (state.skillId != 0)
						SkillEngine.getInstance().applyEffectDirectly(state.skillId, killer, killer);
					return;
				}
			}
		}
	}
}
