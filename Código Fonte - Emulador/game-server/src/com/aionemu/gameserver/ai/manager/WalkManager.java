package com.aionemu.gameserver.ai.manager;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.lostacademy.nav.NavData;
import com.lostacademy.nav.NavService;
import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.ai.AIState;
import com.aionemu.gameserver.ai.AISubState;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.configs.main.AIConfig;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.geoEngine.collision.CollisionIntention;
import com.aionemu.gameserver.geoEngine.collision.IgnoreProperties;
import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.templates.walker.RouteStep;
import com.aionemu.gameserver.model.templates.walker.WalkerTemplate;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.geo.GeoService;

/**
 * @author Lost Academy Team & Durak
 */
public class WalkManager {

	private static final Logger log = LoggerFactory.getLogger(WalkManager.class);
	public static final int DEFAULT_FALLBACK_RANDOM_WALK = 6;

	public static byte RANDOM_WALK_GEO_FLAGS = (byte) (CollisionIntention.CANT_SEE_COLLISIONS.getId() | CollisionIntention.WALK.getId() | CollisionIntention.PHYSICAL_SEE_THROUGH.getId());

	/**
	 * Fallback for NPCs whose walker_id does not exist in WALKER_DATA.
	 * Logs an info message and enables random walk instead.
	 */
	public static void fallbackToRandomWalk(Npc npc, String walkerId) {
		if (npc == null || npc.getSpawn() == null || walkerId == null)
			return;
		log.debug("Missing walker template '{}' for NPC {} ({}) at map {}. Falling back to random walk.",
			walkerId, npc.getNpcId(), npc.getName(), npc.getWorldId());
		if (npc.getSpawn().getRandomWalkRange() <= 0) {
			npc.getSpawn().setRandomWalk(DEFAULT_FALLBACK_RANDOM_WALK);
		}
		npc.getSpawn().setWalkerId(null);
	}

	/**
	 * @return True, if the npc started walking. False if walking is disabled, not supported, or the npc is already walking.
	 */
	public static boolean startWalking(NpcAI npcAI) {
		if (!AIConfig.ACTIVE_NPC_MOVEMENT || !npcAI.getOwner().isSpawned())
			return false;
		return startRandomWalking(npcAI) || startRouteWalking(npcAI);
	}

	private static boolean startRandomWalking(NpcAI npcAI) {
		if (!npcAI.getOwner().isRandomWalker())
			return false;
		if (!npcAI.setStateIfNot(AIState.WALKING) || !npcAI.setSubStateIfNot(AISubState.WALK_RANDOM))
			return false;
		EmoteManager.emoteStartWalking(npcAI.getOwner());
		chooseNextRandomPoint(npcAI);
		return true;
	}

	private static boolean startRouteWalking(NpcAI npcAI) {
		Npc owner = npcAI.getOwner();
		if (!owner.isPathWalker())
			return false;
		if (owner.getMoveController().getWalkerTemplate() == null) {
			String walkerId = owner.getSpawn().getWalkerId();
			WalkerTemplate template = DataManager.WALKER_DATA.getWalkerTemplate(walkerId);
			if (template == null) {
				fallbackToRandomWalk(owner, walkerId);
				return startRandomWalking(npcAI);
			}
			owner.getMoveController().setWalkerTemplate(template, 0);
		}
		if (!npcAI.setStateIfNot(AIState.WALKING) || !npcAI.setSubStateIfNot(AISubState.WALK_PATH))
			return false;
		RouteStep nextStep = findNextRoutStep(owner);
		owner.getMoveController().setRouteStep(nextStep);
		EmoteManager.emoteStartWalking(npcAI.getOwner());
		npcAI.getOwner().getMoveController().moveToNextPoint();
		return true;
	}

	/**
	 * @param npcAI
	 * @param x
	 * @param y
	 * @param z
	 */
	public static void startForcedWalking(NpcAI npcAI, float x, float y, float z) {
		npcAI.setStateIfNot(AIState.FORCED_WALKING);
		npcAI.setSubStateIfNot(AISubState.NONE);
		EmoteManager.emoteStartWalking(npcAI.getOwner());
		npcAI.getOwner().getMoveController().forcedMoveToPoint(x, y, z);
	}

	/**
	 * @param owner
	 * @return
	 */
	protected static RouteStep findNextRoutStep(Npc owner) {
		RouteStep currentStep = owner.getMoveController().getCurrentStep();
		RouteStep nextStep = null;
		if (currentStep.getStepIndex() != 0) {
			nextStep = findNextRouteStepAfterPause(owner, currentStep);
		} else {
			nextStep = findClosestRouteStep(owner);
		}
		return nextStep;
	}

	/**
	 * @param owner
	 * @return
	 */
	protected static RouteStep findClosestRouteStep(Npc owner) {
		List<RouteStep> route = owner.getMoveController().getWalkerTemplate().getRouteSteps();
		RouteStep nextStep = null;
		if (owner.getWalkerGroup() != null) {
			nextStep = route.get(owner.getWalkerGroup().getGroupStep());
		} else {
			double closestDist = 0;
			float x = owner.getX();
			float y = owner.getY();
			float z = owner.getZ();
			for (RouteStep step : route) {
				double stepDist = PositionUtil.getDistance(x, y, z, step.getX(), step.getY(), step.getZ());
				if (closestDist == 0 || stepDist < closestDist) {
					closestDist = stepDist;
					nextStep = step;
				}
			}
		}
		return nextStep;
	}

	/**
	 * @param owner
	 * @param route
	 * @param currentStep
	 * @return
	 */
	protected static RouteStep findNextRouteStepAfterPause(Npc owner, RouteStep currentStep) {
		if (PositionUtil.isInRange(owner, currentStep.getX(), currentStep.getY(), currentStep.getZ(), 1)) {
			List<RouteStep> route = owner.getMoveController().getWalkerTemplate().getRouteSteps();
			if (currentStep.isLastStep())
				return route.get(0);
			else
				return route.get(currentStep.getStepIndex() + 1);
		}
		return currentStep;
	}

	/**
	 * @param npcAI
	 */
	public static void targetReached(final NpcAI npcAI) {
		if (npcAI.isInState(AIState.WALKING)) {
			switch (npcAI.getSubState()) {
				case WALK_PATH:
					npcAI.getOwner().updateKnownlist();
					if (npcAI.getOwner().getWalkerGroup() != null) {
						npcAI.getOwner().getWalkerGroup().targetReached(npcAI);
					} else {
						chooseNextRouteStep(npcAI);
					}
					break;
				case WALK_WAIT_GROUP:
					npcAI.setSubStateIfNot(AISubState.WALK_PATH);
					chooseNextRouteStep(npcAI);
					break;
				case WALK_RANDOM:
					chooseNextRandomPoint(npcAI);
					break;
				case TALK:
					npcAI.setStateIfNot(AIState.IDLE);
					npcAI.getOwner().getMoveController().abortMove();
					break;
			}
		} else if (npcAI.isInState(AIState.FORCED_WALKING)) {
			npcAI.getOwner().getMoveController().abortMove();
			npcAI.setStateIfNot(AIState.IDLE);
			npcAI.think();
		}
	}

	/**
	 * @param npcAI
	 */
	protected static void chooseNextRouteStep(NpcAI npcAI) {
		RouteStep chegada = npcAI.getOwner().getMoveController().getCurrentStep();
		int walkPause = npcAI.getOwner().getWalkerGroup() != null ? npcAI.getOwner().getWalkerGroup().getRestTime(npcAI.getOwner(), chegada)
			: chegada.getRestTime();
		if (walkPause == 0) {
			npcAI.getOwner().getMoveController().resetMove();
			if (npcAI.getOwner().getMoveController().isNextRouteStepChosen())
				npcAI.getOwner().getMoveController().moveToNextPoint();
		} else {
			npcAI.getOwner().getMoveController().abortMove();
			if (npcAI.getOwner().getMoveController().isNextRouteStepChosen()) {
				ThreadPoolManager.getInstance().schedule(new Runnable() {

					@Override
					public void run() {
						if (npcAI.isInState(AIState.WALKING)) {
							npcAI.getOwner().getMoveController().moveToNextPoint();
						}
					}
				}, walkPause);
			}
		}
	}

	/**
	 * @param npcAI
	 */
	private static void chooseNextRandomPoint(NpcAI npcAI) {
		Npc owner = npcAI.getOwner();
		owner.getMoveController().abortMove();

		ThreadPoolManager.getInstance().schedule(() -> {
			if (!npcAI.isInState(AIState.WALKING))
				return;
			int randomWalkRange = Math.max(1, owner.getSpawn().getRandomWalkRange());
			int diameter = randomWalkRange * 2;
			float spawnX = owner.getSpawn().getX();
			float spawnY = owner.getSpawn().getY();
			float maxAllowedZDelta = Math.max(4.0f, randomWalkRange * 0.85f);
			boolean hasNavMap = GeoDataConfig.GEO_NAV_ENABLE && NavData.getInstance().getNavMap(owner.getWorldId()) != null;

			for (int attempt = 0; attempt < 6; attempt++) {
				float nextX = Rnd.nextFloat(diameter) - randomWalkRange + spawnX;
				float nextY = Rnd.nextFloat(diameter) - randomWalkRange + spawnY;
				if (PositionUtil.getDistance(owner.getX(), owner.getY(), nextX, nextY) < 1.0) {
					continue;
				}

				if (hasNavMap) {
					float targetZ = NavService.getInstance().getNavSurfaceZ(owner.getWorldId(), nextX, nextY, owner.getZ());
					if (Float.isNaN(targetZ) && GeoDataConfig.GEO_ENABLE) {
						targetZ = GeoService.getInstance().getValidGroundZ(owner.getWorldId(), nextX, nextY, owner.getZ(), owner.getInstanceId());
					}
					if (Float.isNaN(targetZ) || Math.abs(targetZ - owner.getZ()) > maxAllowedZDelta) {
						continue;
					}
					float[][] navPath = NavService.getInstance().navigateToLocation(owner, nextX, nextY, targetZ);
					if (navPath != null && navPath.length > 0) {
						float[] lastWp = navPath[navPath.length - 1];
						float distToSpawn = (float) PositionUtil.getDistance(lastWp[0], lastWp[1], spawnX, spawnY);
						float distFromOwner = (float) PositionUtil.getDistance(owner.getX(), owner.getY(), lastWp[0], lastWp[1]);
						if (distToSpawn <= randomWalkRange * 1.5f && distFromOwner >= 0.8f) {
							float validEndZ = NavService.getInstance().getNavSurfaceZ(owner.getWorldId(), lastWp[0], lastWp[1], lastWp[2]);
							if (!Float.isNaN(validEndZ)) {
								lastWp[2] = validEndZ;
							}
							owner.getMoveController().moveToPoint(lastWp[0], lastWp[1], lastWp[2]);
							return;
						}
					}
				} else if (GeoDataConfig.GEO_ENABLE && GeoDataConfig.GEO_NPC_MOVE) {
					Vector3f loc = GeoService.getInstance().getClosestCollision(
							owner, nextX, nextY, owner.getZ(), true, RANDOM_WALK_GEO_FLAGS, IgnoreProperties.of(owner.getRace()));
					float validZ = GeoService.getInstance().getValidGroundZ(owner.getWorldId(), loc.x, loc.y, loc.z, owner.getInstanceId());
					if (!Float.isNaN(validZ) && Math.abs(validZ - owner.getZ()) <= maxAllowedZDelta
							&& PositionUtil.getDistance(owner.getX(), owner.getY(), loc.x, loc.y) >= 0.8f) {
						owner.getMoveController().moveToPoint(loc.x, loc.y, validZ);
						return;
					}
				} else {
					owner.getMoveController().moveToPoint(nextX, nextY, owner.getZ());
					return;
				}
			}
			// If all candidate random points were blocked or off-mesh, wait for the next random walk cycle
			chooseNextRandomPoint(npcAI);
		}, Rnd.get(AIConfig.MINIMIMUM_DELAY, AIConfig.MAXIMUM_DELAY) * 1000L);
	}

	/**
	 * @param npcAI
	 */
	public static void stopWalking(NpcAI npcAI) {
		npcAI.getOwner().getMoveController().abortMove();
		npcAI.setStateIfNot(AIState.IDLE);
		if (npcAI.getSubState() != AISubState.FREEZE)
			npcAI.setSubStateIfNot(AISubState.NONE);
		EmoteManager.emoteStopWalking(npcAI.getOwner());
	}

	/**
	 * @param npcAI
	 * @return
	 */
	public static boolean isArrivedAtPoint(NpcAI npcAI) {
		return npcAI.getOwner().getMoveController().isReachedPoint();
	}

	private static float[] selectNextNavPoint(Npc owner, float[][] navPath, float minDistance) {
		if (navPath == null || navPath.length == 0)
			return null;
		float[] lastWp = navPath[navPath.length - 1];
		return (lastWp != null && lastWp.length >= 3) ? lastWp : null;
	}
}
