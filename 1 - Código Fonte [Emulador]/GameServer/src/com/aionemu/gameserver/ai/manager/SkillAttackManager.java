package com.aionemu.gameserver.ai.manager;

import com.aionemu.gameserver.ai.AILogger;
import com.aionemu.gameserver.ai.AISubState;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.skill.NpcSkillEntry;
import com.aionemu.gameserver.model.skill.NpcSkillList;
import com.aionemu.gameserver.skillengine.effect.AbnormalState;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.skillengine.model.SkillType;
import com.aionemu.gameserver.utils.MathUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;

public class SkillAttackManager
{
	public static void performAttack(NpcAI npcAI, int delay) {
		if (npcAI.getOwner().getObjectTemplate().getAttackRange() == 0) {
			if (npcAI.getOwner().getTarget() != null && !MathUtil.isInRange(npcAI.getOwner(), npcAI.getOwner().getTarget(), npcAI.getOwner().getAggroRange())) {
				npcAI.onGeneralEvent(AIEventType.TARGET_TOOFAR);
				npcAI.getOwner().getController().cancelCurrentSkill();
				return;
			}
		} if (npcAI.setSubStateIfNot(AISubState.CAST)) {
			if (delay > 0) {
				ThreadPoolManager.getInstance().schedule(new SkillAction(npcAI), delay + DataManager.SKILL_DATA.getSkillTemplate(npcAI.getSkillId()).getDuration());
			} else {
				skillAction(npcAI);
			}
		}
	}
	
	protected static void skillAction(NpcAI npcAI) {
		Creature target = (Creature) npcAI.getOwner().getTarget();
		if (npcAI.getOwner().getObjectTemplate().getAttackRange() == 0) {
			if (npcAI.getOwner().getTarget() != null && !MathUtil.isInRange(npcAI.getOwner(), npcAI.getOwner().getTarget(), npcAI.getOwner().getAggroRange())) {
				npcAI.onGeneralEvent(AIEventType.TARGET_TOOFAR);
				npcAI.getOwner().getController().cancelCurrentSkill();
				return;
			}
		}
		if (target != null && !target.getLifeStats().isAlreadyDead()) {
			final int skillId = npcAI.getSkillId();
			final int skillLevel = npcAI.getSkillLevel();
			SkillTemplate template = DataManager.SKILL_DATA.getSkillTemplate(skillId);
			int duration = template.getDuration();
			if (npcAI.isLogging()) {
				AILogger.info(npcAI, "Using skill " + skillId + " level: " + skillLevel + " duration: " + duration);
			}
			switch (template.getSubType()) {
				case BUFF:
					switch (template.getProperties().getFirstTarget()) {
						case ME:
							if (npcAI.getOwner().getEffectController().isAbnormalPresentBySkillId(skillId)) {
								afterUseSkill(npcAI);
								return;
							}
						break;
						default:
						if (target.getEffectController().isAbnormalPresentBySkillId(skillId)) {
							afterUseSkill(npcAI);
							return;
						}
					}
					break;
			}
			boolean success = npcAI.getOwner().getController().useSkill(skillId, skillLevel);
			if (!success) {
				afterUseSkill(npcAI);
			}
		} else {
			npcAI.setSubStateIfNot(AISubState.NONE);
			npcAI.onGeneralEvent(AIEventType.TARGET_GIVEUP);
		}
	}
	
	public static void afterUseSkill(NpcAI npcAI) {
		npcAI.setSubStateIfNot(AISubState.NONE);
		npcAI.onGeneralEvent(AIEventType.ATTACK_COMPLETE);
	}
	
	public static NpcSkillEntry chooseNextSkill(NpcAI npcAI) {
		if (npcAI.isInSubState(AISubState.CAST)) {
			return null;
		}
		Npc owner = npcAI.getOwner();
		NpcSkillList skillList = owner.getSkillList();
		if (skillList == null || skillList.size() == 0) {
			return null;
		} if (owner.getGameStats().canUseNextSkill()) {
			NpcSkillEntry npcSkill = skillList.getRandomSkill();
			if (npcSkill != null) {
				int currentHpPercent = owner.getLifeStats().getHpPercentage();
				if (npcSkill.isReady(currentHpPercent, System.currentTimeMillis() - owner.getGameStats().getFightStartingTime())) {
					SkillTemplate template = npcSkill.getSkillTemplate();
					if ((template.getType() == SkillType.MAGICAL && owner.getEffectController().isAbnormalSet(AbnormalState.SILENCE))
					|| (template.getType() == SkillType.PHYSICAL && owner.getEffectController().isAbnormalSet(AbnormalState.BIND))
					|| (owner.getEffectController().isUnderFear()))
					return null;
					npcSkill.setLastTimeUsed();
					return npcSkill;
				}
			}
		}
		return null;
	}
	
	private final static class SkillAction implements Runnable {
		private NpcAI npcAI;
		SkillAction(NpcAI npcAI) {
			this.npcAI = npcAI;
		}
		
		@Override
		public void run() {
			skillAction(npcAI);
			npcAI = null;
		}
	}
}