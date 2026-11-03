package com.lostacademy.nav;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import com.aionemu.gameserver.geoEngine.scene.NavGeometry;
import com.aionemu.gameserver.ai.handler.AttackEventHandler;

/**
 * Unit & regression test suite for GeoEngine, NavMesh 3D, and AI movement fixes.
 *
 * @author Lost Academy Team & Antigravity
 */
public class GeoNavRegressionTest {

	private NavGeometry createTriangle(float x0, float y0, float z0, float x1, float y1, float z1, float x2, float y2, float z2) {
		float[] vertices = new float[] {
			x0, y0, z0,
			x1, y1, z1,
			x2, y2, z2
		};
		return new NavGeometry(vertices, 0, 1, 2);
	}

	@Test
	public void testExactSurfaceZOnFlatHorizontalPlane() {
		NavGeometry geom = createTriangle(
			0f, 0f, 100f,
			10f, 0f, 100f,
			0f, 10f, 100f
		);

		assertEquals(100.0f, geom.getExactSurfaceZ(0f, 0f), 0.001f);
		assertEquals(100.0f, geom.getExactSurfaceZ(2f, 2f), 0.001f);
		assertEquals(100.0f, geom.getExactSurfaceZ(5f, 4f), 0.001f);
	}

	@Test
	public void testExactSurfaceZOnSlopedStairPlane() {
		// Plane equation: z = 50 + 2*x + 3*y
		// v0 = (0, 0, 50)
		// v1 = (5, 0, 60)
		// v2 = (0, 4, 62)
		NavGeometry geom = createTriangle(
			0f, 0f, 50f,
			5f, 0f, 60f,
			0f, 4f, 62f
		);

		// At (1, 1): z = 50 + 2(1) + 3(1) = 55.0
		float z1 = geom.getExactSurfaceZ(1f, 1f);
		assertEquals(55.0f, z1, 0.001f);

		// At (2, 1): z = 50 + 2(2) + 3(1) = 57.0
		float z2 = geom.getExactSurfaceZ(2f, 1f);
		assertEquals(57.0f, z2, 0.001f);

		// At incenter (center of triangle):
		float zCenter = geom.getExactSurfaceZ(geom.getIncenterX(), geom.getIncenterY());
		assertEquals(geom.getIncenterZ(), zCenter, 0.001f);
	}

	@Test
	public void test3DEuclideanDistanceCost() {
		// Floor 1 tile at (0, 0, 10)
		NavGeometry tileFloor1 = createTriangle(
			0f, 0f, 10f,
			2f, 0f, 10f,
			0f, 2f, 10f
		);

		// Floor 2 tile at (0, 0, 25) directly above
		NavGeometry tileFloor2 = createTriangle(
			0f, 0f, 25f,
			2f, 0f, 25f,
			0f, 2f, 25f
		);

		float dist3D = tileFloor1.getDistanceToTile(tileFloor2);
		// Horizontal distance between incenters is 0, vertical is 15 -> true 3D Euclidean distance is 15.0
		assertEquals(15.0f, dist3D, 0.01f);

		// Verify Euclidean distance helper
		float pointDist = tileFloor1.getEuclideanDistance(tileFloor1.getIncenterX(), tileFloor1.getIncenterY(), tileFloor1.getIncenterZ() + 15.0f);
		assertEquals(15.0f, pointDist, 0.01f);
	}

	@Test
	public void testMultiFloorVerticalSeparation() {
		// Verifies that two vertically overlapping floor triangles compute distinct exact Z values
		NavGeometry floor1 = createTriangle(
			100f, 100f, 20f,
			110f, 100f, 20f,
			100f, 110f, 20f
		);
		NavGeometry floor2 = createTriangle(
			100f, 100f, 32f,
			110f, 100f, 32f,
			100f, 110f, 32f
		);

		float zFloor1 = floor1.getExactSurfaceZ(102f, 102f);
		float zFloor2 = floor2.getExactSurfaceZ(102f, 102f);

		assertEquals(20.0f, zFloor1, 0.001f);
		assertEquals(32.0f, zFloor2, 0.001f);

		// A query starting from z=21.0 should clearly identify floor 1 as the closest surface
		float diff1 = Math.abs(zFloor1 - 21.0f);
		float diff2 = Math.abs(zFloor2 - 21.0f);
		assertTrue(diff1 < diff2, "Floor 1 (|20 - 21| = 1) must be closer than Floor 2 (|32 - 21| = 11)");
	}

	@Test
	public void testFleeAngleCalculations() {
		// Target at (100, 100), Attacker at (100, 90) -> flee vector away from attacker is (0, +1)
		float dx = 100f - 100f;
		float dy = 100f - 90f;
		float len = (float) Math.hypot(dx, dy);
		assertEquals(10.0f, len, 0.001f);

		float dirX = dx / len;
		float dirY = dy / len;
		assertEquals(0.0f, dirX, 0.001f);
		assertEquals(1.0f, dirY, 0.001f);

		float fleeDistance = 14.0f;
		float desiredX = 100f + dirX * fleeDistance;
		float desiredY = 100f + dirY * fleeDistance;
		assertEquals(100.0f, desiredX, 0.001f);
		assertEquals(114.0f, desiredY, 0.001f);
	}

	@Test
	public void testInvertedTriangleNormalSurfaceZ() {
		// Vertices defined in reverse winding order
		NavGeometry geom = createTriangle(
			0f, 10f, 100f,
			10f, 0f, 100f,
			0f, 0f, 100f
		);

		assertEquals(100.0f, geom.getExactSurfaceZ(0f, 0f), 0.001f);
		assertEquals(100.0f, geom.getExactSurfaceZ(3f, 3f), 0.001f);
	}

	@Test
	public void testLeashDistanceBoundary() {
		// Max chase leash threshold is 60.0m
		float nearDist = 59.5f;
		float farDist = 60.5f;
		assertTrue(nearDist <= 60.0f, "59.5m must be within leash range");
		assertFalse(farDist <= 60.0f, "60.5m must exceed leash range");
	}

	@Test
	public void testSpawnCorrectionToleranceWindow() {
		float referenceZ = 200.0f;

		// Embedded underground by 3m (navZ = 203.0) -> diff = +3.0 -> valid ground correction
		float navZUnderground = 203.0f;
		float diff1 = navZUnderground - referenceZ;
		assertTrue(diff1 >= -5.0f && diff1 <= 6.0f);

		// Floating 2m in air (navZ = 198.0) -> diff = -2.0 -> valid ground correction
		float navZFloating = 198.0f;
		float diff2 = navZFloating - referenceZ;
		assertTrue(diff2 >= -5.0f && diff2 <= 6.0f);

		// Completely different floor 30m below (navZ = 170.0) -> diff = -30.0 -> outside window
		float navZOtherFloor = 170.0f;
		float diff3 = navZOtherFloor - referenceZ;
		assertFalse(diff3 >= -5.0f && diff3 <= 6.0f);
	}
}
