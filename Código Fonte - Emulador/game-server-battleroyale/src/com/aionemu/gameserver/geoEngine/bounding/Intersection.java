package com.aionemu.gameserver.geoEngine.bounding;

import static java.lang.Math.max;
import static java.lang.Math.min;

import com.aionemu.gameserver.geoEngine.math.FastMath;
import com.aionemu.gameserver.geoEngine.math.Plane;
import com.aionemu.gameserver.geoEngine.math.Vector3f;

/**
 * Utility methods for computing intersection between bounding volumes and triangles.
 *
 * @author KAMIDAKI
 */
public class Intersection {

	private static final void findMinMax(float x0, float x1, float x2, Vector3f minMax) {
		minMax.set(x0, x0, 0);
		if (x1 < minMax.x) {
			minMax.setX(x1);
		}
		if (x1 > minMax.y) {
			minMax.setY(x1);
		}
		if (x2 < minMax.x) {
			minMax.setX(x2);
		}
		if (x2 > minMax.y) {
			minMax.setY(x2);
		}
	}

	public static final boolean intersect(BoundingBox bbox, Vector3f v1, Vector3f v2, Vector3f v3) {
		Vector3f tmp0 = new Vector3f(), tmp1 = new Vector3f(), tmp2 = new Vector3f();
		Vector3f e0 = new Vector3f(), e1 = new Vector3f(), e2 = new Vector3f();
		Vector3f minMax = new Vector3f();

		Vector3f center = bbox.getCenter();
		Vector3f extent = bbox.getExtent(null);

		v1.subtract(center, tmp0);
		v2.subtract(center, tmp1);
		v3.subtract(center, tmp2);

			tmp1.subtract(tmp0, e0);
			tmp2.subtract(tmp1, e1);
			tmp0.subtract(tmp2, e2);

			float min, max;
			float p0, p1, p2, rad;
			float fex = FastMath.abs(e0.x);
			float fey = FastMath.abs(e0.y);
			float fez = FastMath.abs(e0.z);

			p0 = e0.z * tmp0.y - e0.y * tmp0.z;
			p2 = e0.z * tmp2.y - e0.y * tmp2.z;
			min = min(p0, p2);
			max = max(p0, p2);
			rad = fez * extent.y + fey * extent.z;
			if (min > rad || max < -rad) {
				return false;
			}

			p0 = -e0.z * tmp0.x + e0.x * tmp0.z;
			p2 = -e0.z * tmp2.x + e0.x * tmp2.z;
			min = min(p0, p2);
			max = max(p0, p2);
			rad = fez * extent.x + fex * extent.z;
			if (min > rad || max < -rad) {
				return false;
			}

			p1 = e0.y * tmp1.x - e0.x * tmp1.y;
			p2 = e0.y * tmp2.x - e0.x * tmp2.y;
			min = min(p1, p2);
			max = max(p1, p2);
			rad = fey * extent.x + fex * extent.y;
			if (min > rad || max < -rad) {
				return false;
			}

			fex = FastMath.abs(e1.x);
			fey = FastMath.abs(e1.y);
			fez = FastMath.abs(e1.z);

			p0 = e1.z * tmp0.y - e1.y * tmp0.z;
			p2 = e1.z * tmp2.y - e1.y * tmp2.z;
			min = min(p0, p2);
			max = max(p0, p2);
			rad = fez * extent.y + fey * extent.z;
			if (min > rad || max < -rad) {
				return false;
			}

			p0 = -e1.z * tmp0.x + e1.x * tmp0.z;
			p2 = -e1.z * tmp2.x + e1.x * tmp2.z;
			min = min(p0, p2);
			max = max(p0, p2);
			rad = fez * extent.x + fex * extent.z;
			if (min > rad || max < -rad) {
				return false;
			}

			p0 = e1.y * tmp0.x - e1.x * tmp0.y;
			p1 = e1.y * tmp1.x - e1.x * tmp1.y;
			min = min(p0, p1);
			max = max(p0, p1);
			rad = fey * extent.x + fex * extent.y;
			if (min > rad || max < -rad) {
				return false;
			}

			fex = FastMath.abs(e2.x);
			fey = FastMath.abs(e2.y);
			fez = FastMath.abs(e2.z);

			p0 = e2.z * tmp0.y - e2.y * tmp0.z;
			p1 = e2.z * tmp1.y - e2.y * tmp1.z;
			min = min(p0, p1);
			max = max(p0, p1);
			rad = fez * extent.y + fey * extent.z;
			if (min > rad || max < -rad) {
				return false;
			}

			p0 = -e2.z * tmp0.x + e2.x * tmp0.z;
			p1 = -e2.z * tmp1.x + e2.x * tmp1.z;
			min = min(p0, p1);
			max = max(p0, p1);
			rad = fez * extent.x + fex * extent.y;
			if (min > rad || max < -rad) {
				return false;
			}

			p1 = e2.y * tmp1.x - e2.x * tmp1.y;
			p2 = e2.y * tmp2.x - e2.x * tmp2.y;
			min = min(p1, p2);
			max = max(p1, p2);
			rad = fey * extent.x + fex * extent.y;
			if (min > rad || max < -rad) {
				return false;
			}

			findMinMax(tmp0.x, tmp1.x, tmp2.x, minMax);
			if (minMax.x > extent.x || minMax.y < -extent.x) {
				return false;
			}

			findMinMax(tmp0.y, tmp1.y, tmp2.y, minMax);
			if (minMax.x > extent.y || minMax.y < -extent.y) {
				return false;
			}

			findMinMax(tmp0.z, tmp1.z, tmp2.z, minMax);
			if (minMax.x > extent.z || minMax.y < -extent.z) {
				return false;
			}

		Plane p = new Plane();
		p.setPlanePoints(v1, v2, v3);
		if (bbox.whichSide(p) == Plane.Side.Negative) {
			return false;
		}

		return true;
	}
}
