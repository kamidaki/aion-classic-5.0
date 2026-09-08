package com.aionemu.gameserver.controllers.movement;

import java.util.LinkedList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.ai.AILogger;
import com.aionemu.gameserver.ai.AIState;
import com.aionemu.gameserver.ai.AISubState;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.handler.TargetEventHandler;
import com.aionemu.gameserver.ai.manager.WalkManager;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.geoEngine.collision.IgnoreProperties;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.geometry.Point3D;
import com.aionemu.gameserver.model.stats.calc.Stat2;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import com.aionemu.gameserver.model.templates.walker.RouteStep;
import com.aionemu.gameserver.model.templates.walker.WalkerTemplate;
import com.aionemu.gameserver.model.templates.walker.WalkerTemplate.LoopType;
import com.aionemu.gameserver.model.templates.zone.Point2D;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MOVE;
import com.aionemu.gameserver.spawnengine.WalkerFormator;
import com.aionemu.gameserver.spawnengine.WalkerGroup;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.geo.GeoService;
import com.lostacademy.eleanor.Global;
import com.lostacademy.eleanor.processors.movement.motor.FollowMotor;
import com.lostacademy.nav.NavService;

/**
 * @author Lost Academy Team & Durak
 */
public class NpcMoveController extends CreatureMoveController<Npc> {

	private static final Logger log = LoggerFactory.getLogger(NpcMoveController.class);
	private static final float MOVE_OFFSET = 0.05f;
	private static final int MAX_GEO_POINT_DISTANCE = 5;

	private Destination destination = Destination.TARGET_OBJECT;

	private float pointX;
	private float pointY;
	private float pointZ;
	private boolean nextPointFromGeo;
	private boolean isStop;

	private LinkedList<Point3D> lastSteps;

	private WalkerTemplate walkerTemplate;
	private RouteStep currentStep;
	private FollowMotor _followMotor;

	private volatile boolean cachedPathValid;
	private volatile float[][] cachedPath;

	public NpcMoveController(Npc owner) {
		super(owner);
	}

	private enum Destination {
		TARGET_OBJECT,
		POINT,
		FORCED_POINT
	}

	/**
	 * Move to current target
	 */
	public void moveToTargetObject() {
		if (started.compareAndSet(false, true)) {
			if (owner.getAi().isLogging()) {
				AILogger.moveinfo(owner, "MC: moveToTarget started");
			}
			destination = Destination.TARGET_OBJECT;
			clearCachedPath();
			updateLastMove();
			owner.getController().onStartMove();
		}
	}

	public boolean moveToPoint(float x, float y, float z) {
		boolean startedMoving = started.compareAndSet(false, true);
		if (!startedMoving && destination != Destination.POINT)
			return false;
		if (owner.getAi().isLogging()) {
			AILogger.moveinfo(owner, "MC: moveToPoint (startedMoving=" + startedMoving + ")");
		}
		destination = Destination.POINT;
		clearCachedPath();
		cancelFollow();
		pointX = x;
		pointY = y;
		pointZ = z;
		updateLastMove();
		if (startedMoving)
			owner.getController().onStartMove();
		return true;
	}

	public void forcedMoveToPoint(float x, float y, float z) {
		if (started.compareAndSet(false, true)) {
			if (owner.getAi().isLogging()) {
				AILogger.moveinfo(owner, "MC: forcedMoveToPoint started");
			}
			destination = Destination.FORCED_POINT;
			clearCachedPath();
			cancelFollow();
			pointX = x;
			pointY = y;
			pointZ = z;
			updateLastMove();
			owner.getController().onStartMove();
		}
	}

	public void moveToNextPoint() {
		if (started.compareAndSet(false, true)) {
			if (owner.getAi().isLogging()) {
				AILogger.moveinfo(owner, "MC: moveToNextPoint started");
			}
			destination = Destination.POINT;
			clearCachedPath();
			cancelFollow();
			updateLastMove();
			owner.getController().onStartMove();
		}
	}

	@Override
	public void moveToDestination() {
		if (owner.getAi().isLogging()) {
			AILogger.moveinfo(owner, "moveToDestination destination: " + destination);
		}
		if (owner.isDead()) {
			abortMove();
			return;
		}
		if (!owner.canPerformMove()) {
			if (owner.getAi().isLogging()) {
				AILogger.moveinfo(owner, "moveToDestination can't perform move");
			}
			if (started.compareAndSet(true, false)) {
				cancelFollow();
				clearCachedPath();
				setAndSendStopMove(owner);
				updateLastMove();
			}
			return;
		}
		if (started.compareAndSet(false, true)) {
			updateLastMove();
			setAndSendStartMove(owner);
		}

		switch (destination) {
			case TARGET_OBJECT:
				VisibleObject target = owner.getTarget();
				if (target == null || !(target instanceof Creature)) {
					cancelFollow();
					clearCachedPath();
					return;
				}

				Creature creature = (Creature) target;
				float targetX = creature.getX();
				float targetY = creature.getY();
				float targetZ = creature.getZ();

				// Invalida rota do NavMesh se o alvo se moveu mais de 1.5m
				if (PositionUtil.getDistance(targetX, targetY, targetZ, pointX, pointY, pointZ) > 1.5f) {
					pointX = targetX;
					pointY = targetY;
					pointZ = targetZ;
					clearCachedPath();
				}

				// ========================================================
				// CAMADA 1: NAVMESH (3D Navigation Mesh Pathfinding)
				// ========================================================
				if (GeoDataConfig.GEO_NAV_ENABLE) {
					if (!cachedPathValid || cachedPath == null) {
						cachedPath = NavService.getInstance().navigateToTarget(owner, creature);
						cachedPathValid = true;
					}

					if (cachedPath != null && !isNavFailurePath(cachedPath) && cachedPath.length > 0) {
						// NavMesh encontrou uma rota válida: cancela Eleanor
						cancelFollow();

						// Pula waypoints intermediários já alcançados
						while (cachedPath != null && cachedPath.length > 1
								&& PositionUtil.isInRange(owner, cachedPath[0][0], cachedPath[0][1], cachedPath[0][2], 0.5f)) {
							float[][] temp = new float[cachedPath.length - 1][];
							System.arraycopy(cachedPath, 1, temp, 0, cachedPath.length - 1);
							cachedPath = temp;
						}

						float[] nextPoint = cachedPath[0];
						moveToLocation(nextPoint[0], nextPoint[1], nextPoint[2]);
						break;
					}
				}

				// ========================================================
				// CAMADA 2: FALLBACK PARA ELEANOR (FollowMotor / Pathfind)
				// ========================================================
				// Se NavMesh falhar ou não tiver dados, tenta Eleanor
				clearCachedPath();
				if (owner.getAi().getState() == AIState.FOLLOWING) {
					cancelFollow();
					fallbackToNormalMove(target);
				} else {
					applyFollow(target);
				}
				break;

			case POINT:
			case FORCED_POINT:
				cancelFollow();
				if (GeoDataConfig.GEO_NAV_ENABLE && destination == Destination.POINT) {
					if (!cachedPathValid || cachedPath == null) {
						cachedPath = NavService.getInstance().navigateToLocation(owner, pointX, pointY, pointZ);
						cachedPathValid = true;
					}
					if (cachedPath != null && !isNavFailurePath(cachedPath) && cachedPath.length > 0) {
						while (cachedPath != null && cachedPath.length > 1
								&& PositionUtil.isInRange(owner, cachedPath[0][0], cachedPath[0][1], cachedPath[0][2], 0.5f)) {
							float[][] temp = new float[cachedPath.length - 1][];
							System.arraycopy(cachedPath, 1, temp, 0, cachedPath.length - 1);
							cachedPath = temp;
						}
						float[] nextPoint = cachedPath[0];
						moveToLocation(nextPoint[0], nextPoint[1], nextPoint[2]);
						break;
					}
				}
				moveToLocation(pointX, pointY, pointZ);
				break;
		}
		updateLastMove();
	}

	private boolean isOnGround(Creature creature) {
		return !creature.isFlying() && !creature.getMoveController().isJumping() && (creature.getMoveController().getMovementMask() & MovementMask.FALL) == 0;
	}

	/**
	 * Sets pointX, pointY and pointZ to valid geo coordinates near or at given position. Tries to detect and stop at cliffs or steep hills.
	 *
	 * @return True if new geo point was set, false if old one was kept (either because it's still valid or needs to be rechecked at the next interval).
	 */
	private boolean trySetValidGeoPoint(float targetX, float targetY) {
		if (pointX == 0 && pointY == 0 && pointZ == 0) {
			pointX = owner.getX();
			pointY = owner.getY();
			pointZ = owner.getZ();
			owner.getGameStats().setNextGeoZUpdate(0);
		}
		long nowMillis = System.currentTimeMillis();
		if (nowMillis < owner.getGameStats().getNextGeoZUpdate())
			return false;
		float distance2D = (float) PositionUtil.getDistance(pointX, pointY, targetX, targetY);
		if (distance2D < MOVE_CHECK_OFFSET)
			return false; // no need to recalculate
		if (distance2D > MAX_GEO_POINT_DISTANCE) {
			double angleRadians = Math.toRadians(PositionUtil.calculateAngleFrom(pointX, pointY, targetX, targetY));
			targetX = pointX + (float) (Math.cos(angleRadians) * MAX_GEO_POINT_DISTANCE);
			targetY = pointY + (float) (Math.sin(angleRadians) * MAX_GEO_POINT_DISTANCE);
			distance2D = MAX_GEO_POINT_DISTANCE;
		}
		float maxZDiff = distance2D + MOVE_CHECK_OFFSET;
		float geoZ = GeoService.getInstance().getZ(owner.getWorldId(), targetX, targetY, pointZ + maxZDiff, pointZ - maxZDiff, owner.getInstanceId());
		if (Float.isNaN(geoZ)) {
			owner.getGameStats().setNextGeoZUpdate(nowMillis + 1000);
			return false;
		}
		pointX = targetX;
		pointY = targetY;
		pointZ = geoZ;
		owner.getGameStats().setNextGeoZUpdate(nowMillis + 500);
		return true;
	}

	private void moveToLocation(float targetX, float targetY, float targetZ) {
		float ownerX = owner.getX();
		float ownerY = owner.getY();
		float ownerZ = owner.getZ();

		if (owner.getAi().isLogging()) {
			AILogger.moveinfo(owner, "OLD targetDestX: " + targetDestX + " targetDestY: " + targetDestY + " targetDestZ " + targetDestZ);
		}

		// to prevent broken walkers in case of activating/deactivating zones
		if (targetX == 0 && targetY == 0) {
			targetX = owner.getSpawn().getX();
			targetY = owner.getSpawn().getY();
			targetZ = owner.getSpawn().getZ();
			clearBackSteps();
		} else if (owner.getAi().getState() == AIState.FIGHT || owner.getAi().getState() == AIState.FOLLOWING) {
			tryStoreStep(targetX, targetY, targetZ);
		}

		boolean destinationChanged = targetX != targetDestX || targetY != targetDestY || targetZ != targetDestZ;
		if (targetX != targetDestX || targetY != targetDestY)
			heading = PositionUtil.getHeadingTowards(ownerX, ownerY, targetX, targetY);

		targetDestX = targetX;
		targetDestY = targetY;
		targetDestZ = targetZ;

		if (owner.getAi().isLogging()) {
			AILogger.moveinfo(owner, "ownerX=" + ownerX + " ownerY=" + ownerY + " ownerZ=" + ownerZ);
			AILogger.moveinfo(owner, "targetDestX: " + targetDestX + " targetDestY: " + targetDestY + " targetDestZ " + targetDestZ);
		}

		float currentSpeed = owner.getGameStats().getMovementSpeedFloat();
		float futureDistPassed = currentSpeed * (System.currentTimeMillis() - lastMoveUpdate) / 1000f;
		float dist = (float) PositionUtil.getDistance(ownerX, ownerY, ownerZ, targetX, targetY, targetZ);

		if (owner.getAi().isLogging()) {
			AILogger.moveinfo(owner, "futureDist: " + futureDistPassed + " dist: " + dist);
		}

		if (dist == 0) {
			if (owner.getAi().getState() == AIState.RETURNING) {
				if (owner.getAi().isLogging()) {
					AILogger.moveinfo(owner, "State RETURNING: abort move");
				}
				TargetEventHandler.onTargetReached((NpcAI) owner.getAi());
			}
			return;
		}

		if (futureDistPassed > dist) {
			futureDistPassed = dist;
		}

		if (futureDistPassed == dist && GeoDataConfig.GEO_NAV_ENABLE
				&& (destination == Destination.TARGET_OBJECT || destination == Destination.POINT)) {
			if (cachedPath != null && cachedPath.length > 0) {
				float[][] tempCache = new float[cachedPath.length - 1][];
				if (tempCache.length > 0) {
					System.arraycopy(cachedPath, 1, tempCache, 0, cachedPath.length - 1);
					cachedPath = tempCache;
				} else {
					cachedPath = null;
					cachedPathValid = false;
				}
			}
		}

		float distFraction = futureDistPassed / dist;
		float newX = (targetDestX - ownerX) * distFraction + ownerX;
		float newY = (targetDestY - ownerY) * distFraction + ownerY;
		float newZ = (targetDestZ - ownerZ) * distFraction + ownerZ;
		if (GeoDataConfig.GEO_NPC_MOVE && GeoDataConfig.GEO_ENABLE && owner.getAi().getSubState() != AISubState.WALK_PATH
			&& owner.getAi().getState() != AIState.RETURNING && owner.getGameStats().getNextGeoZUpdate() < System.currentTimeMillis()) {
			// fix Z if npc doesn't move to spawn point
			if (owner.getSpawn().getX() != targetDestX || owner.getSpawn().getY() != targetDestY || owner.getSpawn().getZ() != targetDestZ) {
				float geoZ = GeoService.getInstance().getZ(owner.getWorldId(), newX, newY, newZ + 2, Math.min(newZ, ownerZ) - 2, owner.getInstanceId());
				if (!Float.isNaN(geoZ)) {
					if (Math.abs(newZ - geoZ) > 1)
						destinationChanged = true;
					newZ = geoZ;
					boolean isXYDestinationReached = PositionUtil.getDistance(newX, newY, pointX, pointY) < MOVE_OFFSET;
					if (isXYDestinationReached && !PositionUtil.isInRange(newX, newY, newZ, pointX, pointY, pointZ, MOVE_OFFSET))
						pointZ = newZ; // original pointZ is unreachable, override it so isReachedPoint() can return true
				}
			}
			owner.getGameStats().setNextGeoZUpdate(System.currentTimeMillis() + 1000);
		}
		if (owner.getAi().isLogging()) {
			AILogger.moveinfo(owner, "newX=" + newX + " newY=" + newY + " newZ=" + newZ + " mask=" + movementMask);
		}

		World.getInstance().updatePosition(owner, newX, newY, newZ, heading, false);

		byte newMask = getMoveMask(destinationChanged);
		if (movementMask != newMask || destinationChanged) {
			if (movementMask != newMask) {
				if (owner.getAi().isLogging()) {
					AILogger.moveinfo(owner, "oldMask=" + movementMask + " newMask=" + newMask);
				}
				movementMask = newMask;
			}
			PacketSendUtility.broadcastPacket(owner, new SM_MOVE(owner));
		}
	}

	private byte getMoveMask(boolean directionChanged) {
		if (directionChanged)
			return MovementMask.NPC_STARTMOVE;
		else if (owner.getAi().getState() == AIState.RETURNING)
			return MovementMask.NPC_RUN_FAST;
		else if (owner.getAi().getState() == AIState.FOLLOWING)
			return MovementMask.NPC_WALK_SLOW;

		byte mask = MovementMask.IMMEDIATE;
		final Stat2 stat = owner.getGameStats().getMovementSpeed();
		if (owner.isInState(CreatureState.WEAPON_EQUIPPED)) {
			mask = stat.getBonus() < 0 ? MovementMask.NPC_RUN_FAST : MovementMask.NPC_RUN_SLOW;
		} else if (owner.isInState(CreatureState.WALK_MODE) || owner.isInState(CreatureState.ACTIVE)) {
			mask = stat.getBonus() < 0 ? MovementMask.NPC_WALK_FAST : MovementMask.NPC_WALK_SLOW;
		}
		if (owner.isFlying())
			mask |= MovementMask.GLIDE;
		return mask;
	}

	@Override
	public void abortMove() {
		if (!started.get())
			return;
		resetMove();
		setAndSendStopMove(owner);
	}

	/**
	 * Initialize values to default ones
	 */
	public void resetMove() {
		if (owner.getAi().isLogging()) {
			AILogger.moveinfo(owner, "MC perform stop");
		}
		clearCachedPath();
		cancelFollow();
		owner.getController().onStopMove();
		started.set(false);
		targetDestX = 0;
		targetDestY = 0;
		targetDestZ = 0;
		pointX = 0;
		pointY = 0;
		pointZ = 0;
		nextPointFromGeo = false;
	}

	public WalkerTemplate getWalkerTemplate() {
		return walkerTemplate;
	}

	public void setWalkerTemplate(WalkerTemplate walkerTemplate, int stepIndex) {
		this.walkerTemplate = walkerTemplate;
		this.currentStep = walkerTemplate.getRouteStep(stepIndex);
	}

	public void setRouteStep(RouteStep step) {
		Point2D dest = null;
		if (owner.getWalkerGroup() != null) {
			dest = WalkerGroup.getLinePoint(new Point2D(currentStep.getX(), currentStep.getY()), new Point2D(step.getX(), step.getY()),
				owner.getWalkerGroup().getClusterData(owner));
			this.pointZ = currentStep.getZ();
			owner.getWalkerGroup().setStep(owner, step.getStepIndex());
		} else {
			this.pointZ = step.getZ();
			this.isStop = walkerTemplate.getLoopType() == LoopType.NONE && step.isLastStep();
		}
		this.currentStep = step;
		this.pointX = dest == null ? step.getX() : dest.getX();
		this.pointY = dest == null ? step.getY() : dest.getY();
		this.destination = Destination.POINT;
	}

	public RouteStep getCurrentStep() {
		return currentStep;
	}

	public boolean isReachedPoint() {
		return PositionUtil.isInRange(owner, pointX, pointY, pointZ, MOVE_OFFSET);
	}

	public boolean isNextRouteStepChosen() {
		if (isStop) {
			WalkManager.stopWalking((NpcAI) owner.getAi());
			return false;
		}
		if (walkerTemplate == null) {
			WalkManager.stopWalking((NpcAI) owner.getAi());
			if (WalkerFormator.processClusteredNpc(owner, owner.getWorldId(), owner.getInstanceId()))
				return false;

			setWalkerTemplate(DataManager.WALKER_DATA.getWalkerTemplate(owner.getSpawn().getWalkerId()), 0);
			if (walkerTemplate == null) {
				log.warn("Bad Walker Id: " + owner.getSpawn().getWalkerId() + " - point: " + currentStep.getStepIndex());
				return false;
			}
		}
		List<RouteStep> routeSteps = walkerTemplate.getRouteSteps();
		RouteStep nextStep = currentStep.isLastStep() ? routeSteps.get(0) : routeSteps.get(currentStep.getStepIndex() + 1);
		setRouteStep(nextStep);
		return true;
	}

	public boolean isChangingDirection() {
		return currentStep.getStepIndex() == 0;
	}

	@Override
	public final float getTargetX2() {
		return started.get() ? targetDestX : owner.getX();
	}

	@Override
	public final float getTargetY2() {
		return started.get() ? targetDestY : owner.getY();
	}

	@Override
	public final float getTargetZ2() {
		return started.get() ? targetDestZ : owner.getZ();
	}

	public boolean isStop() {
		return isStop;
	}

	private synchronized void tryStoreStep(float x, float y, float z) {
		if (lastSteps == null)
			lastSteps = new LinkedList<>();
		Point3D lastStep = lastSteps.isEmpty() ? null : lastSteps.getLast();
		if (lastStep == null || !PositionUtil.isInRange(lastStep.getX(), lastStep.getY(), lastStep.getZ(), x, y, z, 10)) {
			if (owner.getAi().isLogging()) {
				AILogger.moveinfo(owner, "store back step: X=" + owner.getX() + " Y=" + owner.getY() + " Z=" + owner.getZ());
			}
			lastSteps.add(new Point3D(x, y, z));
			if (lastSteps.size() > 10)
				lastSteps.removeFirst();
		}
	}

	public synchronized void returnToLastStepOrSpawn() {
		SpawnTemplate spawn = owner.getSpawn();
		Point3D step = lastSteps == null || lastSteps.isEmpty() ? null : lastSteps.removeLast();
		if (step != null && !lastSteps.isEmpty() && PositionUtil.isInRange(owner, step.getX(), step.getY(), step.getZ(), 2))
			step = lastSteps.removeLast();
		if (step == null || GeoService.getInstance().canSee(owner, spawn.getX(), spawn.getY(), spawn.getZ(), IgnoreProperties.ANY_RACE)) {
			targetDestX = spawn.getX();
			targetDestY = spawn.getY();
			targetDestZ = spawn.getZ();
			if (owner.getAi().isLogging())
				AILogger.moveinfo(owner, "recall back step: spawn point");
		} else {
			targetDestX = step.getX();
			targetDestY = step.getY();
			targetDestZ = step.getZ();
			if (owner.getAi().isLogging())
				AILogger.moveinfo(owner, "recall back step: X=" + step.getX() + " Y=" + step.getY() + " Z=" + step.getZ());
		}
		moveToPoint(targetDestX, targetDestY, targetDestZ);
	}

	public synchronized void clearBackSteps() {
		lastSteps = null;
		movementMask = MovementMask.IMMEDIATE;
	}

	public void applyFollow(VisibleObject target) {
		if (_followMotor != null && _followMotor.getTarget() == target)
			return;

		if (_followMotor != null) {
			_followMotor.stop();
		}

		if (Global.MovementProcessor == null) {
			fallbackToNormalMove(target);
			return;
		}

		_followMotor = new FollowMotor(Global.MovementProcessor, owner, target);
		_followMotor.start();
	}

	public void cancelFollow() {
		if (_followMotor != null) {
			_followMotor.stop();
			_followMotor = null;
		}
	}

	public void fallbackToNormalMove(VisibleObject target) {
		if (target == null)
			return;
		if (!PositionUtil.isInRange(target, pointX, pointY, pointZ, MOVE_CHECK_OFFSET)) {
			if (GeoDataConfig.GEO_NPC_MOVE && !owner.isInFlyingState() && target instanceof Creature creature && (nextPointFromGeo || (nextPointFromGeo = !isOnGround(creature)))) {
				if (trySetValidGeoPoint(target.getX(), target.getY()) && nextPointFromGeo)
					nextPointFromGeo = !isOnGround(creature);
			} else {
				pointX = target.getX();
				pointY = target.getY();
				pointZ = target.getZ();
			}
		}
		moveToLocation(pointX, pointY, pointZ);
	}

	private boolean isNavFailurePath(float[][] path) {
		if (path == null || path.length == 0) {
			return true;
		}
		if (path.length == 1) {
			float[] point = path[0];
			if (point.length >= 3) {
				double distance = PositionUtil.getDistance(owner.getX(), owner.getY(), owner.getZ(),
						point[0], point[1], point[2]);
				return distance <= 1.0f;
			}
		}
		return false;
	}

	public void clearCachedPath() {
		cachedPath = null;
		cachedPathValid = false;
	}
}
