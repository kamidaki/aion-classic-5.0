package com.aionemu.gameserver.geoEngine.collision;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;

/**
 * Holds the results of a collision query against a scene graph.
 * Migrated from 4.8: added IgnoreProperties, invalidateSlopingSurface support.
 */
public class CollisionResults implements Iterable<CollisionResult> {

	private static final double SLOPING_SURFACE_ANGLE_RAD = Math.toRadians(45); // players can't walk or stand on surfaces with >= 45 deg elevation

	private final ArrayList<CollisionResult> results = new ArrayList<>();
	private boolean sorted = true;
	private final boolean onlyFirst;
	private final byte intentions;
	private final int instanceId;
	private final IgnoreProperties ignoreProperties;
	private boolean invalidateSlopingSurface;

	// ---- Constructors (5.0 legacy signature kept for backward compatibility) ----

	/** Legacy 5.0 constructor: no IgnoreProperties */
	public CollisionResults(byte intentions, boolean searchFirst, int instanceId) {
		this(intentions, instanceId, searchFirst, null);
	}

	// ---- 4.8 constructors ----

	public CollisionResults(byte intentions, int instanceId, IgnoreProperties ignoreProperties) {
		this(intentions, instanceId, false, ignoreProperties);
	}

	public CollisionResults(byte intentions, int instanceId) {
		this(intentions, instanceId, false, null);
	}

	public CollisionResults(byte intentions, int instanceId, boolean searchFirst) {
		this(intentions, instanceId, searchFirst, null);
	}

	public CollisionResults(byte intentions, int instanceId, boolean searchFirst, IgnoreProperties ignoreProperties) {
		this.intentions = intentions;
		this.instanceId = instanceId;
		this.onlyFirst = searchFirst;
		this.ignoreProperties = ignoreProperties;
	}

	public void clear() {
		results.clear();
	}

	@Override
	public Iterator<CollisionResult> iterator() {
		if (!sorted) {
			results.sort(null);
			sorted = true;
		}

		return results.iterator();
	}

	public void addCollision(CollisionResult result) {
		if (Float.isNaN(result.getDistance())) {
			return;
		}
		results.add(result);
		if (!onlyFirst)
			sorted = false;
	}

	public int size() {
		return results.size();
	}

	public CollisionResult getClosestCollision() {
		if (size() == 0)
			return null;

		if (!sorted) {
			results.sort(null);
			sorted = true;
		}

		return results.get(0);
	}

	public CollisionResult getFarthestCollision() {
		if (size() == 0)
			return null;

		if (!sorted) {
			results.sort(null);
			sorted = true;
		}

		return results.get(size() - 1);
	}

	public CollisionResult getCollision(int index) {
		if (!sorted) {
			Collections.sort(results);
			sorted = true;
		}

		return results.get(index);
	}

	/**
	 * Internal use only.
	 */
	public CollisionResult getCollisionDirect(int index) {
		return results.get(index);
	}

	@Override
	public String toString() {
		StringBuilder sb = new StringBuilder();
		sb.append("CollisionResults[");
		for (CollisionResult result : results) {
			sb.append(result).append(", ");
		}
		if (results.size() > 0)
			sb.setLength(sb.length() - 2);

		sb.append("]");
		return sb.toString();
	}

	/**
	 * @return True if the results should only contain one collision max.
	 */
	public boolean isOnlyFirst() {
		return onlyFirst;
	}

	/**
	 * @return the collision intentions bitmask
	 */
	public byte getIntentions() {
		return intentions;
	}

	public int getInstanceId() {
		return instanceId;
	}

	/**
	 * @return IgnoreProperties for race/instance-based collision filtering, or null
	 */
	public IgnoreProperties getIgnoreProperties() {
		return this.ignoreProperties;
	}

	/**
	 * @return true if sloping surface collisions (>= 45°) should be invalidated
	 */
	public boolean shouldInvalidateSlopingSurface() {
		return invalidateSlopingSurface;
	}

	public double getSlopingSurfaceAngleRad() {
		return SLOPING_SURFACE_ANGLE_RAD;
	}

	public void setInvalidateSlopingSurface(boolean invalidateSlopingSurface) {
		this.invalidateSlopingSurface = invalidateSlopingSurface;
	}
}
