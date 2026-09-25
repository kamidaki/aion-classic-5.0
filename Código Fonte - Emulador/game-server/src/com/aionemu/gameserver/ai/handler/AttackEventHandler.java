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

	private static final float[] FLEE_ANGLE_OFFSETS_DEG = { 0f, 35f, -35f, 70f, -70f, 110f, -110f, 145f, -145f };
	private static final float[] FLEE_DISTANCES = { 14.0f, 9.0f };

	public static boolean isMaxFleeLeashExceeded(Npc npc, Creature attacker) {
		if (npc == null || attacker == null || attacker.isDead() || !npc.canSee(attacker)) {
			return true;
		}
		if (!PositionUtil.isInRange(npc, attacker, 60.0f, false)) {
			return true;
		}
		double distanceToHome = npc.getDistanceToSpawnLocation();
		int chaseHome = 150;
		if (npc.getPosition() != null && npc.getPosition().getWorldMapInstance() != null
				&& npc.getPosition().getWorldMapInstance().getTemplate() != null
				&& npc.getPosition().getWorldMapInstance().getTemplate().getAiInfo() != null) {
			chaseHome = Math.max(150, npc.getPosition().getWorldMapInstance().getTemplate().getAiInfo().getChaseHome());
		}
		return distanceToHome > chaseHome;
	}

	public static void onPlayerFlightStateChanged(NpcAI npcAI, Player player, boolean airborne) {
		if (npcAI == null || player == null) {
			return;
		}
		Npc npc = npcAI.getOwner();
		if (npc == null || npc.isDead() || !npc.isSpawned() || !npcAI.canThink()) {
			return;
		}
		boolean isTargetingOrHating = player.equals(npc.getTarget()) || npc.getAggroList().isHating(player);
		if (!isTargetingOrHating) {
			return;
		}
		if (airborne) {
			if (isGroundNpc(npc) && !isWithinAttackRange(npc, player)) {
				fleeFromAirborneAttacker(npcAI, player);
			}
		} else {
			if (npcAI.isInState(AIState.FEAR) && !npc.getEffectController().isAbnormalSet(AbnormalState.FEAR)) {
				resumeCombatFromAirborneFlee(npcAI, player);
			}
		}
	}

	public static void onFleeDestinationReached(NpcAI npcAI) {
		if (npcAI == null) {
			return;
		}
		Npc npc = npcAI.getOwner();
		if (npc == null || npc.isDead() || !npc.isSpawned() || !npcAI.isInState(AIState.FEAR)) {
			return;
		}
		if (npc.getEffectController().isAbnormalSet(AbnormalState.FEAR)) {
			return;
		}
		Creature attacker = ( npc.getTarget() instanceof Creature c ) ? c : npc.getAggroList().getTarget(AggroTarget.MOST_HATED);
		if (attacker == null || attacker.isDead() || isMaxFleeLeashExceeded(npc, attacker)) {
			abandonFleeAndReturnHome(npcAI, attacker);
			return;
		}
		if (!(attacker instanceof Player player && player.isFlying()) || isWithinAttackRange(npc, attacker)) {
			resumeCombatFromAirborneFlee(npcAI, attacker);
			return;
		}
		if (!PositionUtil.isInRange(npc, attacker, 25.0f, false)) {
			// Safe holding distance reached while keeping target/aggro locked
			return;
		}
		selectAndMoveToFleeDestination(npc, attacker);
	}

	public static void resumeCombatFromAirborneFlee(NpcAI npcAI, Creature attacker) {
		Npc npc = npcAI.getOwner();
		if (npc == null || npc.isDead() || !npc.isSpawned() || !npcAI.canThink()) {
			return;
		}
		if (npc.getEffectController().isAbnormalSet(AbnormalState.FEAR)) {
			return;
		}
		if (attacker == null || attacker.isDead() || isMaxFleeLeashExceeded(npc, attacker)) {
			abandonFleeAndReturnHome(npcAI, attacker);
			return;
		}
		if (!npc.getAggroList().isHating(attacker)) {
			npc.getAggroList().addHate(attacker, 1);
		}
		npc.setTarget(attacker);
		npc.getGameStats().renewLastAttackedTime();
		npcAI.setStateIfNot(AIState.FIGHT);
		npcAI.setSubStateIfNot(AISubState.NONE);
		if (npcAI.isMoveSupported()) {
			npc.getMoveController().moveToTargetObject();
		}
		AttackManager.scheduleNextAttack(npcAI);
	}

	private static void abandonFleeAndReturnHome(NpcAI npcAI, Creature attacker) {
		Npc npc = npcAI.getOwner();
		if (npc == null) {
			return;
		}
		if (attacker != null) {
			npc.getAggroList().stopHating(attacker);
		}
		npcAI.setStateIfNot(AIState.IDLE);
		npcAI.setSubStateIfNot(AISubState.NONE);
		npc.clearQueuedSkills();
		npc.getGameStats().setLastSkill(null);
		npc.getGameStats().resetFightStats();

		Creature mostHated = npc.getAggroList().getTarget(AggroTarget.MOST_HATED);
		if (mostHated != null && !mostHated.isDead() && npc.canSee(mostHated) && !isMaxFleeLeashExceeded(npc, mostHated)) {
			npc.setTarget(mostHated);
			if (mostHated instanceof Player p && p.isFlying() && isGroundNpc(npc) && !isWithinAttackRange(npc, p)) {
				fleeFromAirborneAttacker(npcAI, p);
			} else {
				resumeCombatFromAirborneFlee(npcAI, mostHated);
			}
		} else {
			npc.setTarget(null);
			npcAI.onGeneralEvent(AIEventType.ATTACK_FINISH);
			npcAI.onGeneralEvent(npc.isAtSpawnLocation() ? AIEventType.BACK_HOME : AIEventType.NOT_AT_HOME);
		}
	}

	private static void selectAndMoveToFleeDestination(Npc npc, Creature attacker) {
		float dx = npc.getX() - attacker.getX();
		float dy = npc.getY() - attacker.getY();
		float len = (float) Math.hypot(dx, dy);
		if (len > 0.001f) {
			dx /= len;
			dy /= len;
		} else {
			dx = 1.0f;
			dy = 0.0f;
		}

		double baseAngleRad = Math.atan2(dy, dx);
		float targetX = Float.NaN;
		float targetY = Float.NaN;
		float targetZ = Float.NaN;

		// 1. Search reachable NavMesh paths across candidate flee angles away from the airborne player
		if (GeoDataConfig.GEO_NAV_ENABLE) {
			outer:
			for (float dist : FLEE_DISTANCES) {
				for (float offsetDeg : FLEE_ANGLE_OFFSETS_DEG) {
					double rad = baseAngleRad + Math.toRadians(offsetDeg);
					float candX = npc.getX() + (float) Math.cos(rad) * dist;
					float candY = npc.getY() + (float) Math.sin(rad) * dist;
					float candZ = NavService.getInstance().getNavSurfaceZ(npc.getWorldId(), candX, candY, npc.getZ());
					if (Float.isNaN(candZ) && GeoDataConfig.GEO_ENABLE) {
						candZ = GeoService.getInstance().getValidGroundZ(npc.getWorldId(), candX, candY, npc.getZ(), npc.getInstanceId());
					}
					if (Float.isNaN(candZ)) {
						continue;
					}
					float[][] path = NavService.getInstance().navigateToLocation(npc, candX, candY, candZ);
					if (path != null && path.length > 0) {
						float[] finalWp = path[path.length - 1];
						double pathDist2D = PositionUtil.getDistance(npc.getX(), npc.getY(), finalWp[0], finalWp[1]);
						if (pathDist2D >= 2.0) {
							targetX = finalWp[0];
							targetY = finalWp[1];
							targetZ = finalWp[2];
							break outer;
						}
					}
				}
			}
		}

		// 2. Fallback to GeoEngine collision step + valid ground Z
		if (Float.isNaN(targetX)) {
			float angle = PositionUtil.calculateAngleFrom(attacker, npc);
			Vector3f stepPoint = GeoService.getInstance().findMovementCollision(npc, angle, 12.0f);
			if (stepPoint != null) {
				targetX = stepPoint.getX();
				targetY = stepPoint.getY();
				targetZ = stepPoint.getZ();
				if (GeoDataConfig.GEO_ENABLE) {
					float geoZ = GeoService.getInstance().getValidGroundZ(npc.getWorldId(), targetX, targetY, targetZ, npc.getInstanceId());
					if (!Float.isNaN(geoZ)) {
						targetZ = geoZ;
					}
				}
			} else {
				targetX = npc.getX() + dx * 10.0f;
				targetY = npc.getY() + dy * 10.0f;
				targetZ = npc.getZ();
			}
		}

		npc.getMoveController().moveToPoint(targetX, targetY, targetZ);
	}

	public static void fleeFromAirborneAttacker(NpcAI npcAI, Creature attacker) {
		Npc npc = npcAI.getOwner();
		if (npc == null || npc.isDead() || !npcAI.canThink()) {
			return;
		}

		if (npcAI.isInState(AIState.WALKING)) {
			WalkManager.stopWalking(npcAI);
		}

		if (isMaxFleeLeashExceeded(npc, attacker)) {
			abandonFleeAndReturnHome(npcAI, attacker);
			return;
		}

		// Preserve aggro and target while fleeing from an airborne player
		if (!npc.getAggroList().isHating(attacker)) {
			npc.getAggroList().addHate(attacker, 1);
		}
		if (npc.getTarget() == null) {
			npc.setTarget(attacker);
		}

		boolean newlyEnteredFlee = npcAI.setStateIfNot(AIState.FEAR);
		npc.getController().abortCast();
		npc.getGameStats().renewLastAttackedTime();

		selectAndMoveToFleeDestination(npc, attacker);

		if (newlyEnteredFlee) {
			scheduleFleeMonitor(npcAI, attacker);
		}
	}

	private static void scheduleFleeMonitor(NpcAI npcAI, Creature attacker) {
		ThreadPoolManager.getInstance().schedule(() -> {
			Npc npc = npcAI.getOwner();
			if (npc == null || npc.isDead() || !npc.isSpawned()) {
				return;
			}
			if (!npcAI.isInState(AIState.FEAR) || npc.getEffectController().isAbnormalSet(AbnormalState.FEAR)) {
				return;
			}

			Creature currentTarget = (npc.getTarget() instanceof Creature c) ? c : attacker;
			if (currentTarget == null || currentTarget.isDead() || isMaxFleeLeashExceeded(npc, currentTarget)) {
				abandonFleeAndReturnHome(npcAI, currentTarget);
				return;
			}

			if (!(currentTarget instanceof Player player && player.isFlying()) || isWithinAttackRange(npc, currentTarget)) {
				resumeCombatFromAirborneFlee(npcAI, currentTarget);
				return;
			}

			npc.getGameStats().renewLastAttackedTime();
			if (!npc.getMoveController().isInMove() && PositionUtil.isInRange(npc, currentTarget, 25.0f, false)) {
				selectAndMoveToFleeDestination(npc, currentTarget);
			}
			scheduleFleeMonitor(npcAI, currentTarget);
		}, 600);
	}
}
