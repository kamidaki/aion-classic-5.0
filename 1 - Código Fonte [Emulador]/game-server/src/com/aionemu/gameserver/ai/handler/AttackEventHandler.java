package com.aionemu.gameserver.ai.handler;

import com.aionemu.gameserver.ai.AILogger;
import com.aionemu.gameserver.ai.AIState;
import com.aionemu.gameserver.ai.AISubState;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.ai.manager.AttackManager;
import com.aionemu.gameserver.ai.manager.EmoteManager;
import com.aionemu.gameserver.ai.manager.WalkManager;
import com.aionemu.gameserver.controllers.attack.AggroTarget;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.skill.NpcSkillEntry;
import com.aionemu.gameserver.skillengine.effect.AbnormalState;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.geo.GeoService;
import com.lostacademy.eleanor.processors.movement.PathfindHelper;
import com.lostacademy.eleanor.utils.GeomUtil;

/**
 * @author Lost Academy Team & Durak
 */
public class AttackEventHandler {

	/**
	 * @param npcAI
	 * @param creature
	 */
	public static void onAttack(NpcAI npcAI, Creature creature) {
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "onAttack");
		}
		if (creature == null || creature.isDead()) {
			return;
		}
		// TODO lock or better switch
		if (npcAI.isInState(AIState.RETURNING)) {
			npcAI.getOwner().getMoveController().abortMove();
			npcAI.setStateIfNot(AIState.IDLE);
			npcAI.onGeneralEvent(AIEventType.NOT_AT_HOME);
			return;
		}
		if (!npcAI.canThink()) {
			return;
		}
		if (npcAI.isInState(AIState.WALKING)) {
			WalkManager.stopWalking(npcAI);
		}
		npcAI.getOwner().getGameStats().renewLastAttackedTime();

		if (creature instanceof Player player && player.isFlying() && isGroundNpc(npcAI.getOwner())) {
			if (!isWithinAttackRange(npcAI.getOwner(), player)) {
				fleeFromAirborneAttacker(npcAI, player);
				return;
			}
		}

		boolean allowFight = npcAI.getState() != AIState.FEAR && !npcAI.getOwner().getEffectController().isAbnormalSet(AbnormalState.FEAR)
				&& npcAI.getState() != AIState.CONFUSE && !npcAI.getOwner().getEffectController().isAbnormalSet(AbnormalState.CONFUSE);
		if (allowFight && npcAI.setStateIfNot(AIState.FIGHT)) {
			if (npcAI.isLogging())
				AILogger.info(npcAI, "onAttack() -> startAttacking");
			npcAI.setSubStateIfNot(AISubState.NONE);
			if (npcAI.getOwner().canSee(creature))
				npcAI.getOwner().setTarget(creature);
			AttackManager.startAttacking(npcAI);
			ShoutEventHandler.onAttackBegin(npcAI);
		}
	}

	/**
	 * @param npcAI
	 */
	public static void onForcedAttack(NpcAI npcAI) {
		onAttack(npcAI, (Creature) npcAI.getOwner().getTarget());
	}

	/**
	 * @param npcAI
	 */
	public static void onAttackComplete(NpcAI npcAI) {
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "onAttackComplete: " + npcAI.getOwner().getGameStats().getLastAttackTimeDelta());
		}
		npcAI.getOwner().getGameStats().renewLastAttackTime();
		AttackManager.scheduleNextAttack(npcAI);
	}

	/**
	 * @param npcAI
	 */
	public static void onFinishAttack(NpcAI npcAI) {
		if (!npcAI.canThink()) {
			return;
		}
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "onFinishAttack");
		}
		Npc npc = npcAI.getOwner();
		EmoteManager.emoteStopAttacking(npc);
		ShoutEventHandler.onAttackEnd(npcAI);
		npc.getController().loseAggro(true);
		npc.setSkillNumber(0);
	}

	public static boolean isGroundNpc(Npc npc) {
		if (npc == null)
			return false;
		return !npc.isInState(CreatureState.FLYING) && (npc.getSpawn() == null || !npc.getSpawn().isAerialSpawn());
	}

	public static float getEffectiveAttackRange(Npc npc) {
		if (npc == null)
			return 2.0f;
		float range = npc.getGameStats().getAttackRange().getCurrent() / 1000.0f;
		if (range <= 0 && npc.getSkillList() != null && !npc.getSkillList().isEmpty()) {
			for (NpcSkillEntry entry : npc.getSkillList().getNpcSkills()) {
				SkillTemplate st = DataManager.SKILL_DATA.getSkillTemplate(entry.getSkillId());
				if (st != null && st.getProperties() != null) {
					int r = st.getProperties().getFirstTargetRange();
					if (r > range) {
						range = r;
					}
				}
			}
		}
		return range > 0 ? range : 2.0f;
	}

	public static boolean isWithinAttackRange(Npc npc, Creature target) {
		if (npc == null || target == null)
			return false;
		float range = getEffectiveAttackRange(npc);
		return PositionUtil.isInAttackRange(npc, target, range);
	}

	public static void fleeFromAirborneAttacker(NpcAI npcAI, Creature attacker) {
		Npc npc = npcAI.getOwner();
		if (npc == null || npc.isDead() || !npcAI.canThink()) {
			return;
		}

		if (npcAI.isInState(AIState.WALKING)) {
			WalkManager.stopWalking(npcAI);
		}

		// Regras rigorosas de fuga contra alvo aéreo inalcançável:
		// 1. Limpar ódio do atacante aéreo para não ficar preso em loop
		npc.getAggroList().stopHating(attacker);
		if (npc.getTarget() != null && npc.getTarget().equals(attacker)) {
			npc.setTarget(null);
		}

		npcAI.setStateIfNot(AIState.FEAR);
		npc.getController().abortCast();
		npc.getGameStats().renewLastAttackedTime();

		Vector3f npcPos = new Vector3f(npc.getX(), npc.getY(), npc.getZ());
		Vector3f attackerPos = new Vector3f(attacker.getX(), attacker.getY(), attacker.getZ());
		Vector3f dirAway = GeomUtil.getDirection3D(attackerPos, npcPos);
		dirAway.z = 0;
		if (dirAway.length() > 0) {
			dirAway.normalizeLocal();
		} else {
			dirAway = new Vector3f(1, 0, 0);
		}

		float fleeDistance = 15.0f;
		Vector3f desiredPoint = GeomUtil.getNextPoint3D(npcPos, dirAway, fleeDistance);

		Vector3f stepPoint = PathfindHelper.selectStep(npc, desiredPoint);
		if (stepPoint == null) {
			float angle = PositionUtil.calculateAngleFrom(attacker, npc);
			stepPoint = GeoService.getInstance().findMovementCollision(npc, angle, fleeDistance);
		}
		if (stepPoint == null) {
			stepPoint = PathfindHelper.getRandomPoint(npc, 5.0f, 15.0f);
		}

		if (stepPoint != null) {
			npc.getMoveController().moveToPoint(stepPoint.getX(), stepPoint.getY(), stepPoint.getZ());
		}

		// Agendar rotina de conclusão da fuga e retorno ao lar
		ThreadPoolManager.getInstance().schedule(() -> {
			if (npc == null || npc.isDead() || !npc.isSpawned()) {
				return;
			}
			if (npc.getEffectController().isAbnormalSet(AbnormalState.FEAR)) {
				return;
			}
			if (npcAI.isInState(AIState.FEAR)) {
				npcAI.setStateIfNot(AIState.IDLE);
				npcAI.setSubStateIfNot(AISubState.NONE);
				npc.clearQueuedSkills();
				npc.getGameStats().setLastSkill(null);
				npc.getGameStats().resetFightStats();

				Creature mostHated = npc.getAggroList().getTarget(AggroTarget.MOST_HATED);
				if (mostHated != null && !mostHated.isDead() && npc.canSee(mostHated)) {
					npcAI.onCreatureEvent(AIEventType.CREATURE_AGGRO, mostHated);
				} else {
					npcAI.onGeneralEvent(AIEventType.ATTACK_FINISH);
					npcAI.onGeneralEvent(npc.isAtSpawnLocation() ? AIEventType.BACK_HOME : AIEventType.NOT_AT_HOME);
				}
			}
		}, 3500);
	}
}
