package com.aionemu.gameserver.geoEngine.collision;

import java.util.Objects;

import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.geoEngine.scene.Geometry;

/**
 * @author Lost Academy Team & Durak
 */
public class CollisionResult implements Comparable<CollisionResult> {

	private final Vector3f contactPoint;
	private final float distance;
	private Geometry geometry;

	public CollisionResult(Vector3f contactPoint, float distance) {
		this.contactPoint = contactPoint;
		this.distance = distance;
	}

	@Override
	public int compareTo(CollisionResult other) {
		return Float.compare(distance, other.distance);
	}

	public void setGeometry(Geometry geom) {
		this.geometry = geom;
	}

	public Vector3f getContactPoint() {
		return contactPoint;
	}

	public Geometry getGeometry() {
		return geometry;
	}

	public float getDistance() {
		return distance;
	}

	@Override
	public boolean equals(Object obj) {
		if (!(obj instanceof CollisionResult)) {
			return false;
		}
		if (this == obj) {
			return true;
		}

		if (distance != ((CollisionResult) obj).distance || !contactPoint.equals(((CollisionResult) obj).contactPoint)) {
			return false;
		}
		return Objects.equals(geometry.getName(), ((CollisionResult) obj).getGeometry().getName());
	}

	@Override
	public int hashCode() {
		return Objects.hash(contactPoint, distance, geometry);
	}
}
