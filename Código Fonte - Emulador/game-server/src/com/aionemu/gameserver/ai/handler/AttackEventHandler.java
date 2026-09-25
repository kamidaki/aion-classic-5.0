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
import com.lostacademy.nav.NavService;
import com.aionemu.gameserver.configs.main.GeoDataConfig;

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

		float dx = npc.getX() - attacker.getX();
		float dy = npc.getY() - attacker.getY();
		float len = (float) Math.sqrt(dx * dx + dy * dy);
		if (len > 0.001f) {
			dx /= len;
			dy /= len;
		} else {
			dx = 1.0f;
			dy = 0.0f;
		}

		float fleeDistance = 15.0f;
		float desiredX = npc.getX() + dx * fleeDistance;
		float desiredY = npc.getY() + dy * fleeDistance;
		float desiredZ = npc.getZ();

		float targetX = desiredX;
		float targetY = desiredY;
		float targetZ = desiredZ;

		// 1. Tentar encontrar rota via NavMesh (.nav)
		boolean movedByNav = false;
		if (GeoDataConfig.GEO_NAV_ENABLE) {
			float navZ = NavService.getInstance().getNavSurfaceZ(npc.getWorldId(), desiredX, desiredY, desiredZ);
			if (Float.isNaN(navZ) && GeoDataConfig.GEO_ENABLE) {
				navZ = GeoService.getInstance().getZ(npc.getWorldId(), desiredX, desiredY, desiredZ, 0.5f, npc.getInstanceId());
			}
			float testZ = Float.isNaN(navZ) ? desiredZ : navZ;
			float[][] path = NavService.getInstance().navigateToLocation(npc, desiredX, desiredY, testZ);
			if (path != null && path.length > 0) {
				targetX = path[0][0];
				targetY = path[0][1];
				targetZ = path[0][2];
				movedByNav = true;
			}
		}
		if (!movedByNav) {
			// 2. Fallback de colisão física via GeoService
			float angle = PositionUtil.calculateAngleFrom(attacker, npc);
			Vector3f stepPoint = GeoService.getInstance().findMovementCollision(npc, angle, fleeDistance);
			if (stepPoint != null) {
				targetX = stepPoint.getX();
				targetY = stepPoint.getY();
				targetZ = stepPoint.getZ();
				if (GeoDataConfig.GEO_ENABLE) {
					float geoZ = GeoService.getInstance().getZ(npc.getWorldId(), targetX, targetY, targetZ, 0.5f, npc.getInstanceId());
					if (!Float.isNaN(geoZ)) {
						targetZ = geoZ;
					}
				}
			}
		}

		npc.getMoveController().moveToPoint(targetX, targetY, targetZ);

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
