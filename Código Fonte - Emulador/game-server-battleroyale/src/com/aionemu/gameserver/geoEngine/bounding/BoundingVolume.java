package com.aionemu.gameserver.geoEngine.bounding;

import java.nio.FloatBuffer;

import com.aionemu.gameserver.geoEngine.collision.Collidable;
import com.aionemu.gameserver.geoEngine.math.Matrix4f;
import com.aionemu.gameserver.geoEngine.math.Ray;
import com.aionemu.gameserver.geoEngine.math.Vector3f;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class BoundingVolume implements Collidable {

	public enum Type {
		Sphere,
		AABB,
		OBB,
		Capsule
	}

	Vector3f center = new Vector3f();

	public BoundingVolume() {
	}

	public BoundingVolume(Vector3f center) {
		this.center.set(center);
	}

	/**
	 * getType returns the type of bounding volume this is.
	 */
	public abstract Type getType();

	/**
	 * <code>transform</code> alters the location of the bounding volume by a rotation, translation and a scalar.
	 * 
	 * @param trans
	 *          the transform to affect the bound.
	 * @param store
	 *          sphere to store result in
	 * @return the new bounding volume.
	 */

	public abstract BoundingVolume transform(Matrix4f trans, BoundingVolume store);

	/**
	 * <code>computeFromPoints</code> generates a bounding volume that encompasses a collection of points.
	 * 
	 * @param points
	 *          the points to contain.
	 */
	public abstract void computeFromPoints(FloatBuffer points);

	/**
	 * <code>mergeLocal</code> combines two bounding volumes into a single bounding volume that contains both this
	 * bounding volume and the parameter volume. The result is stored locally.
	 * 
	 * @param volume
	 *          the volume to combine.
	 * @return this
	 */
	public abstract BoundingVolume mergeLocal(BoundingVolume volume);

	/**
	 * <code>clone</code> creates a new BoundingVolume object containing the same data as this one.
	 * 
	 * @param store
	 *          where to store the cloned information. if null or wrong class, a new store is created.
	 * @return the new BoundingVolume
	 */
	public abstract BoundingVolume clone(BoundingVolume store);

	public final Vector3f getCenter() {
		return center;
	}

	public final Vector3f getCenter(Vector3f store) {
		store.set(center);
		return store;
	}

	public final void setCenter(Vector3f newCenter) {
		center = newCenter;
	}

	/**
	 * Find the distance from the center of this Bounding Volume to the given point.
	 * 
	 * @param point
	 *          The point to get the distance to
	 * @return distance
	 */
	public final float distanceTo(Vector3f point) {
		return center.distance(point);
	}

	/**
	 * Find the squared distance from the center of this Bounding Volume to the given point.
	 * 
	 * @param point
	 *          The point to get the distance to
	 * @return distance
	 */
	public final float distanceSquaredTo(Vector3f point) {
		return center.distanceSquared(point);
	}

	/**
	 * Find the distance from the nearest edge of this Bounding Volume to the given point.
	 * 
	 * @param point
	 *          The point to get the distance to
	 * @return distance
	 */
	public abstract float distanceToEdge(Vector3f point);

	/**
	 * determines if this bounding volume and a second given volume are intersecting. Intersecting being: one volume
	 * contains another, one volume overlaps another or one volume touches another.
	 * 
	 * @param bv
	 *          the second volume to test against.
	 * @return true if this volume intersects the given volume.
	 */
	public abstract boolean intersects(BoundingVolume bv);

	/**
	 * determines if a ray intersects this bounding volume.
	 * 
	 * @param ray
	 *          the ray to test.
	 * @return true if this volume is intersected by a given ray.
	 */
	public abstract boolean intersects(Ray ray);

	/**
	 * determines if this bounding volume and a given bounding box are intersecting.
	 * 
	 * @param bb
	 *          the bounding box to test against.
	 * @return true if this volume intersects the given bounding box.
	 */
	public abstract boolean intersectsBoundingBox(BoundingBox bb);

	/**
	 * determines if a given point is contained within this bounding volume.
	 * 
	 * @param point
	 *          the point to check
	 * @return true if the point lies within this bounding volume.
	 */
	public abstract boolean contains(Vector3f point);

	/**
	 * Determines if a given point intersects (touches or is inside) this bounding volume.
	 * 
	 * @param point
	 *          the point to check
	 * @return true if the point lies within this bounding volume.
	 */
	public abstract boolean intersects(Vector3f point);

	public abstract float getVolume();
}
