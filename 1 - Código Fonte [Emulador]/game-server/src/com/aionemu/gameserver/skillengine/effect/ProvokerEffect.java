package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.controllers.attack.AttackStatus;
import com.aionemu.gameserver.controllers.observer.ActionObserver;
import com.aionemu.gameserver.controllers.observer.ObserverType;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.HitType;
import com.aionemu.gameserver.skillengine.model.ProvokeTarget;
import com.aionemu.gameserver.skillengine.model.SkillType;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.PositionUtil;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ProvokerEffect")
public class ProvokerEffect extends ShieldEffect {

	@XmlAttribute(name = "provoke_target")
	protected ProvokeTarget provokeTarget;
	@XmlAttribute(name = "skill_id")
	protected int skillId;

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}

	@Override
	public void startEffect(Effect effect) {
		Creature effector = effect.getEffector();
		ObserverType observerType;
		if (hitType == HitType.NMLATK || hitType == HitType.BACKATK || hitType == HitType.CRITICAL) {
			observerType = ObserverType.ATTACK;
		} else if (hitType == HitType.EVERYHIT || hitType == null) {
			observerType = ObserverType.ATTACK_DEFEND;
		} else {
			observerType = ObserverType.ATTACKED;
		}
		effect.addObserver(effect.getEffected(), new ActionObserver(observerType) {

			@Override
			public void attack(Creature attacked, int attackSkillId) {
				tryApplyEffect(attacked, attackSkillId, null, effector);
			}

			@Override
			public void attack(Creature attacked, int attackSkillId, AttackStatus status) {
				tryApplyEffect(attacked, attackSkillId, status, effector);
			}

			@Override
			public void attacked(Creature attacker, int attackSkillId) {
				tryApplyEffect(attacker, attackSkillId, null, effector);
			}

			@Override
			public void attacked(Creature attacker, int attackSkillId, AttackStatus status) {
				tryApplyEffect(attacker, attackSkillId, status, effector);
			}

			private void tryApplyEffect(Creature target, int attackSkillId, AttackStatus status, Creature effector) {
				if (shouldApply(effector, target, attackSkillId, status)) {
					if (effector instanceof Player player) {
						PacketSendUtility.sendPacket(player,
							SM_SYSTEM_MESSAGE.STR_SKILL_PROC_EFFECT_OCCURRED(DataManager.SKILL_DATA.getSkillTemplate(skillId).getL10n()));
					}
					SkillEngine.getInstance().applyEffectDirectly(skillId, effector, getProvokeTarget(effector, target));
				}
			}
		});
	}

	private boolean shouldApply(Creature effector, Creature target, int attackSkillId, AttackStatus status) {
		if (provokeTarget == ProvokeTarget.OPPONENT && target == effector)
			return false;
		if (radius > 0 && !PositionUtil.isInRange(effector, target, radius, false))
			return false;
		if (hitType == HitType.DODGEHIT && (status == null || AttackStatus.getBaseStatus(status) != AttackStatus.DODGE))
			return false;
		if (hitType == HitType.PARRYHIT && (status == null || AttackStatus.getBaseStatus(status) != AttackStatus.PARRY))
			return false;
		if (hitType == HitType.CRITICAL) {
			if (attackSkillId == 0)
				return false;
			if (effector instanceof Player player) {
				if (skillId == 9185 && (player.getSkillList().isSkillPresent(4203) || player.getSkillList().isSkillPresent(4204)))
					return false;
				if (skillId == 9187 && player.getSkillList().isSkillPresent(4204))
					return false;
			}
			if (effector.getEffectController().hasAbnormalEffect(9186) || effector.getEffectController().hasAbnormalEffect(9188) || effector.getEffectController().hasAbnormalEffect(9190))
				return false;
			boolean isCrit = status != null && status.isCritical();
			boolean isShockImmune = false;
			if (target != null) {
				var skillTemplate = DataManager.SKILL_DATA.getSkillTemplate(attackSkillId);
				if (skillTemplate != null && hasShockEffect(skillTemplate)) {
					var ec = target.getEffectController();
					isShockImmune = ec.isAbnormalSet(AbnormalState.STUN) || ec.isAbnormalSet(AbnormalState.STUMBLE)
						|| ec.isAbnormalSet(AbnormalState.SPIN) || ec.isAbnormalSet(AbnormalState.OPENAERIAL)
						|| ec.isAbnormalSet(AbnormalState.STAGGER) || ec.isAbnormalSet(AbnormalState.SANCTUARY);
					if (target instanceof com.aionemu.gameserver.model.gameobjects.Npc npc) {
						isShockImmune = isShockImmune || npc.isBoss() || npc.hasStatic();
					}
				}
			}
			if (!isCrit && !isShockImmune)
				return false;
		}
		float chance = hitTypeProb > 100 ? hitTypeProb / 10f : hitTypeProb;
		if (Rnd.chance() >= chance)
			return false;
		if (hitType == null || hitType == HitType.EVERYHIT || hitType == HitType.CRITICAL)
			return true;
		return switch (hitType) {
			case PHHIT -> attackSkillId == 0 || (DataManager.SKILL_DATA.getSkillTemplate(attackSkillId) != null && DataManager.SKILL_DATA.getSkillTemplate(attackSkillId).getType() == SkillType.PHYSICAL);
			case MAHIT -> attackSkillId != 0 && DataManager.SKILL_DATA.getSkillTemplate(attackSkillId) != null && DataManager.SKILL_DATA.getSkillTemplate(attackSkillId).getType() == SkillType.MAGICAL;
			case BACKATK -> PositionUtil.isBehind(effector, target);
			case DODGEHIT, PARRYHIT -> true;
			default -> true;
		};
	}

	private static boolean hasShockEffect(com.aionemu.gameserver.skillengine.model.SkillTemplate st) {
		if (st.getEffects() != null && st.getEffects().getEffects() != null) {
			for (EffectTemplate et : st.getEffects().getEffects()) {
				if (et instanceof StunEffect || et instanceof StumbleEffect || et instanceof SpinEffect || et instanceof OpenAerialEffect || et instanceof ParalyzeEffect || et instanceof StaggerEffect) {
					return true;
				}
			}
		}
		return false;
	}

	private Creature getProvokeTarget(Creature effector, Creature target) {
		return switch (provokeTarget) {
			case ME -> effector;
			case OPPONENT -> target;
		};
	}

	@Override
	public void endEffect(Effect effect) {
	}
}
