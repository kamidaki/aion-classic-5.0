package com.aionemu.gameserver.controllers.movement;

import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;

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
import com.lostacademy.nativepath.NativePathConfig;
import com.lostacademy.nativepath.NativePathService;

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

	/**
	 * Estado imutável da rota NativePath em cache.
	 *
	 * Encapsula path + index num objeto único trocado atomicamente via AtomicReference,
	 * eliminando a race condition entre clearCachedPath() e moveToDestination().
	 * Qualquer thread que lê pathRef.get() obtém um snapshot coerente — não é possível
	 * ver path != null mas index já resetado, ou vice-versa.
	 */
	private static final class PathState {
		final float[][] path;
		final int index;

		PathState(float[][] path, int index) {
			this.path = path;
			this.index = index;
		}

		/** Retorna novo PathState com índice incrementado (imutável). */
		PathState advance() {
			return index < path.length - 1 ? new PathState(path, index + 1) : this;
		}

		/** Retorna o waypoint corrente ou null se path vazio. */
		float[] current() {
			return (path != null && index < path.length) ? path[index] : null;
		}

		/** Verifica se há waypoints restantes acessíveis. */
		boolean hasNext() {
			return path != null && index < path.length;
		}
	}

	/** Referência atômica ao estado da rota — null representa "sem rota válida". */
	private final AtomicReference<PathState> pathRef = new AtomicReference<>(null);
	private long lastPathCalcTime;
	private float lastTargetX;
	private float lastTargetY;
	private float lastTargetZ;

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

				// ========================================================
				// CAMADA ÚNICA: NATIVE-PATH (CryEngine Native Grid 0.5m)
				// Sem canUseDirectTargetMovement — sempre usa A* NativePath.
				// NPC nunca para: se A* falhar, move direto ao alvo sem pausa.
				// ========================================================
				cancelFollow();
				if (NativePathConfig.NATIVE_PATH_ENABLE) {
					long now = System.currentTimeMillis();
					PathState ps = pathRef.get();

					// Rerota se:
					// 1) Não há rota ou waypoints esgotados
					// 2) Alvo moveu-se > 2m desde o cálculo E > 500ms se passaram
					// 3) Tempo excessivo > 1200ms (garante responsividade mesmo parado)
					boolean needRepath = (ps == null || !ps.hasNext());
					if (!needRepath && ps.path != null && ps.path.length > 0) {
						float distFromTargetAtCalc = (float) PositionUtil.getDistance(targetX, targetY, targetZ, lastTargetX, lastTargetY, lastTargetZ);
						if (distFromTargetAtCalc > 2.0f && (now - lastPathCalcTime) >= 500) {
							needRepath = true;
						} else if ((now - lastPathCalcTime) >= 1200) {
							needRepath = true;
						}
					}

					if (needRepath) {
						float[][] newPath = NativePathService.getInstance().navigateToTarget(owner, creature);
						if (newPath != null && newPath.length > 0) {
							lastPathCalcTime = now;
							lastTargetX = targetX;
							lastTargetY = targetY;
							lastTargetZ = targetZ;

							// Waypoint 0 é a posição inicial — pula se o NPC já estiver próximo
							int startIdx = 0;
							if (newPath.length > 1 && PositionUtil.isInRange(owner, newPath[0][0], newPath[0][1], newPath[0][2], 1.2f)) {
								startIdx = 1;
							}
							ps = new PathState(newPath, startIdx);
							pathRef.set(ps);
						} else {
							// A* falhou (mapa sem dados ou rota inacessível):
							// Move diretamente ao alvo — NPC nunca para pra "pensar"
							ps = null;
							pathRef.set(null);
							moveToLocation(targetX, targetY, targetZ);
							break;
						}
					}

					if (ps != null && ps.hasNext()) {
						// Tolerância dinâmica de chegada ao waypoint proporcional à velocidade
						float speed = owner.getGameStats().getMovementSpeedFloat();
						float tolerance = Math.max(1.0f, speed * 0.30f);

						while (ps.hasNext()
								&& ps.index < ps.path.length - 1
								&& PositionUtil.isInRange(owner, ps.current()[0], ps.current()[1], ps.current()[2], tolerance)) {
							ps = ps.advance();
							pathRef.set(ps);
						}

						float[] nextPoint = ps.current();
						if (nextPoint != null) {
							moveToLocation(nextPoint[0], nextPoint[1], nextPoint[2]);
							break;
						}
					}
				}

				// NativePath desativado ou sem waypoints restantes — move direto sem pausa
				moveToLocation(targetX, targetY, targetZ);
				break;

			case POINT:
			case FORCED_POINT:
				cancelFollow();
				if (NativePathConfig.NATIVE_PATH_ENABLE && destination == Destination.POINT) {
					PathState ps = pathRef.get();
					if (ps == null) {
						float[][] newPath = NativePathService.getInstance().navigateToLocation(owner, pointX, pointY, pointZ);
						int startIdx = 0;
						if (newPath != null && newPath.length > 1 && PositionUtil.isInRange(owner, newPath[0][0], newPath[0][1], newPath[0][2], 1.2f)) {
							startIdx = 1;
						}
						ps = (newPath != null && newPath.length > 0) ? new PathState(newPath, startIdx) : null;
						pathRef.set(ps);
					}
					if (ps != null && ps.hasNext()) {
						float speed = owner.getGameStats().getMovementSpeedFloat();
						float tolerance = Math.max(1.2f, speed * 0.35f);

						while (ps.index < ps.path.length - 1
								&& PositionUtil.isInRange(owner, ps.current()[0], ps.current()[1], ps.current()[2], tolerance)) {
							ps = ps.advance();
							pathRef.set(ps);
						}
						float[] nextPoint = ps.current();
						if (nextPoint != null) {
							moveToLocation(nextPoint[0], nextPoint[1], nextPoint[2]);
							break;
						}
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

		if (futureDistPassed == dist && NativePathConfig.NATIVE_PATH_ENABLE
				&& (destination == Destination.TARGET_OBJECT || destination == Destination.POINT)) {
			// Avança índice ao chegar no waypoint atual (operação atômica CAS)
			PathState ps = pathRef.get();
			if (ps != null) {
				if (ps.index < ps.path.length - 1) {
					pathRef.compareAndSet(ps, ps.advance());
				} else {
					pathRef.set(null); // Rota concluída
				}
			}
		}

		float distFraction = futureDistPassed / dist;
		float newX = (targetDestX - ownerX) * distFraction + ownerX;
		float newY = (targetDestY - ownerY) * distFraction + ownerY;
		float newZ = (targetDestZ - ownerZ) * distFraction + ownerZ;

		// Clamping de Z durante AIState.RETURNING para impedir flutuação em linha reta
		if (owner.getAi().getState() == AIState.RETURNING) {
			float surfaceZ = GeoService.getInstance().getZ(owner.getWorldId(), newX, newY, newZ + 3.0f, newZ - 6.0f, owner.getInstanceId());
			if (Float.isNaN(surfaceZ)) {
				surfaceZ = com.lostacademy.nativepath.NativePathService.getInstance().getSurfaceZ(owner.getWorldId(), newX, newY, newZ);
			}
			if (!Float.isNaN(surfaceZ)) {
				newZ = surfaceZ;
			}
		} else if (GeoDataConfig.GEO_NPC_MOVE && GeoDataConfig.GEO_ENABLE && owner.getAi().getSubState() != AISubState.WALK_PATH
			&& owner.getGameStats().getNextGeoZUpdate() < System.currentTimeMillis()) {
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
		this.currentStep = walkerTemplate != null ? walkerTemplate.getRouteStep(stepIndex) : null;
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
			if (owner.getSpawn().getWalkerId() == null)
				return false;
			if (WalkerFormator.processClusteredNpc(owner, owner.getWorldId(), owner.getInstanceId()))
				return false;

			WalkerTemplate template = DataManager.WALKER_DATA.getWalkerTemplate(owner.getSpawn().getWalkerId());
			if (template == null) {
				WalkManager.fallbackToRandomWalk(owner, owner.getSpawn().getWalkerId());
				WalkManager.startWalking((NpcAI) owner.getAi());
				return false;
			}
			setWalkerTemplate(template, 0);
		}
		List<RouteStep> routeSteps = walkerTemplate.getRouteSteps();
		RouteStep nextStep = currentStep.isLastStep() ? routeSteps.get(0) : routeSteps.get(currentStep.getStepIndex() + 1);
		setRouteStep(nextStep);
		return true;
	}

	public boolean isChangingDirection() {
		return currentStep != null && currentStep.getStepIndex() == 0;
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
		cancelFollow();
		SpawnTemplate spawn = owner.getSpawn();
		float spawnX = spawn.getX();
		float spawnY = spawn.getY();
		float spawnZ = spawn.getZ();

		// CAMADA 1: NATIVE-PATH (Obedece o pathfinding nativo CryEngine até o ponto de spawn)
		if (NativePathConfig.NATIVE_PATH_ENABLE) {
			clearCachedPath();
			float[][] newPath = NativePathService.getInstance().navigateToLocation(owner, spawnX, spawnY, spawnZ);
			if (newPath != null && newPath.length > 0) {
				pathRef.set(new PathState(newPath, 0));
				destination = Destination.POINT;
				pointX = spawnX;
				pointY = spawnY;
				pointZ = spawnZ;
				started.set(true);
				owner.getController().onStartMove();
				updateLastMove();
				return;
			}
		}



		// CAMADA 3 & 4: FALLBACK PARA ELEANOR E GEO RETORNO DIRETO
		clearCachedPath();
		Point3D step = lastSteps == null || lastSteps.isEmpty() ? null : lastSteps.removeLast();
		if (step != null && !lastSteps.isEmpty() && PositionUtil.isInRange(owner, step.getX(), step.getY(), step.getZ(), 2))
			step = lastSteps.removeLast();
		if (step == null || GeoService.getInstance().canSee(owner, spawnX, spawnY, spawnZ, IgnoreProperties.ANY_RACE)) {
			targetDestX = spawnX;
			targetDestY = spawnY;
			targetDestZ = spawnZ;
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

	// FIX CAUSA 1: Reduzido de 15m para 4m.
	// A 15m, mobs próximos de obstáculos nunca chegam ao A* — tentam linha reta (canWalkDirectly)
	// e ao falhar caem no FollowMotor/Eleanor que atravessa paredes.
	// A 4m, apenas mobs quase em combate (alcance melee) usam linha reta direta.
	private static final float DIRECT_TARGET_MOVEMENT_MAX_DISTANCE = 4.0f;

	private float calculateMaxZDiff(float distanceXY, Creature target) {
		if (distanceXY < 1.0f) {
			return 1.2f;
		} else if (distanceXY < 3.0f) {
			return 2.0f;
		} else if (distanceXY < 5.0f) {
			return 3.0f;
		} else if (distanceXY < 8.0f) {
			return 5.0f;
		} else if (distanceXY < 10.0f) {
			return 7.0f;
		} else if (distanceXY < 15.0f) {
			return 10.0f;
		} else if (distanceXY < 20.0f) {
			return 15.0f;
		} else {
			return 20.0f;
		}
	}

	private boolean canUseDirectTargetMovement(Creature target, float targetX, float targetY, float targetZ) {
		if (target == null || !target.isSpawned() || target.isDead() || owner.isFlying() || target.isFlying())
			return false;
		double distance = PositionUtil.getDistance(owner.getX(), owner.getY(), owner.getZ(), targetX, targetY, targetZ);
		if (distance > DIRECT_TARGET_MOVEMENT_MAX_DISTANCE)
			return false;
		float maxZDiff = calculateMaxZDiff(
				(float) PositionUtil.getDistance(owner.getX(), owner.getY(), targetX, targetY), target);
		if (Math.abs(owner.getZ() - targetZ) > maxZDiff)
			return false;
		if (NativePathConfig.NATIVE_PATH_ENABLE) {
			return NativePathService.getInstance().canWalkDirectly(owner, targetX, targetY, targetZ);
		}
		return !GeoDataConfig.GEO_ENABLE || GeoService.getInstance().canSee(owner, target);
	}

	private boolean isPathFailure(float[][] path) {
		return path == null || path.length == 0;
	}

	/**
	 * Descarta a rota atual atomicamente.
	 * Seguro para ser chamado de qualquer thread: usa pathRef.set(null) que é atômico.
	 * Não há janela entre "ver path não-null" e "acessar path[index]" de outra thread.
	 */
	public void clearCachedPath() {
		pathRef.set(null);
		lastPathCalcTime = 0;
	}
}
