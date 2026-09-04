package ai;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.ai.handler.*;
import com.aionemu.gameserver.ai.poll.AIAnswer;
import com.aionemu.gameserver.ai.poll.AIAnswers;
import com.aionemu.gameserver.ai.poll.AIQuestion;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.utils.*;
import com.aionemu.gameserver.skillengine.SkillEngine;

@AIName("aggressive")
public class AggressiveNpcAI extends GeneralNpcAI
{
	public AggressiveNpcAI() {
		super();
	}

	public AggressiveNpcAI(Npc owner) {
		super(owner);
	}

	@Override
    protected void handleCreatureSee(Creature creature) {
        CreatureEventHandler.onCreatureSee(this, creature);
    }
	
    @Override
    protected void handleCreatureMoved(Creature creature) {
        CreatureEventHandler.onCreatureMoved(this, creature);
    }
	
	@Override
	protected void handleCreatureAggro(Creature creature) {
		if (canThink()) {
		    AggroEventHandler.onAggro(this, creature);
		}
	}
	
	@Override
	protected boolean handleGuardAgainstAttacker(Creature attacker) {
		return AggroEventHandler.onGuardAgainstAttacker(this, attacker);
	}
	
	protected void creatureNeedHelp(int distance) {
		Creature firstTarget = getAggroList().getMostHated();
		for (VisibleObject object : getKnownList().getKnownObjects().values()) {
			if (object instanceof Npc && isInRange(object, distance)) {
				Npc npc = (Npc) object;
				if ((npc != null) && !npc.getLifeStats().isAlreadyDead()) {
					npc.getAi().onCreatureEvent(AIEventType.CREATURE_AGGRO, firstTarget);
				}
			}
		}
	}
	
	@Override
    protected void handleBackHome() {
        super.handleBackHome();
        if (getSkillList().getUseInSpawnedSkill() != null) {
            final int skillId = getSkillList().getUseInSpawnedSkill().getSkillId();
            final int skillLevel = getSkillList().getSkillLevel(skillId);
            ThreadPoolManager.getInstance().schedule(new Runnable() {
				@Override
				public void run() {
					SkillEngine.getInstance().getSkill(getOwner(), skillId, skillLevel, getOwner()).useNoAnimationSkill();
				}
			}, 3000);
        }
    }
	
    @Override
    protected void handleRespawned() {
        super.handleRespawned();
        if (getSkillList().getUseInSpawnedSkill() != null) {
            final int skillId = getSkillList().getUseInSpawnedSkill().getSkillId();
            final int skillLevel = getSkillList().getSkillLevel(skillId);
			ThreadPoolManager.getInstance().schedule(new Runnable() {
				@Override
				public void run() {
					SkillEngine.getInstance().getSkill(getOwner(), skillId, skillLevel, getOwner()).useNoAnimationSkill();
				}
			}, 3000);
        }
    }
	
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		if (getSkillList().getUseInSpawnedSkill() != null) {
            final int skillId = getSkillList().getUseInSpawnedSkill().getSkillId();
            final int skillLevel = getSkillList().getSkillLevel(skillId);
            ThreadPoolManager.getInstance().schedule(new Runnable() {
				@Override
				public void run() {
					SkillEngine.getInstance().getSkill(getOwner(), skillId, skillLevel, getOwner()).useNoAnimationSkill();
				}
			}, 3000);
        }
	}
	
	@Override
	protected AIAnswer pollInstance(AIQuestion question) {
		switch (question) {
	        case CAN_SPAWN_ON_DAYTIME_CHANGE:
			    return AIAnswers.POSITIVE;
			case SHOULD_DECAY:
			    return AIAnswers.POSITIVE;
			case SHOULD_RESPAWN:
			    return AIAnswers.POSITIVE;
			case SHOULD_REWARD:
			    return AIAnswers.POSITIVE;
			case SHOULD_REWARD_AP:
			    return AIAnswers.POSITIVE;
			case CAN_RESIST_ABNORMAL:
			    return AIAnswers.POSITIVE;
			case CAN_ATTACK_PLAYER:
			    return AIAnswers.POSITIVE;
			default:
				return null;
		}
	}
}