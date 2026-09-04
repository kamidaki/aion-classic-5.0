package com.aionemu.gameserver.geoEngine.math;

/**
 * Simple 3-float array used in geo calculations.
 */
public class Array3f {

	public float a = 0;
	public float b = 0;
	public float c = 0;

	public void reset() {
		a = 0;
		b = 0;
		c = 0;
	}

	/**
	 * Creates a new Array3f instance.
	 * Migrated from 4.8: removed javolution ObjectFactory/Reusable pattern.
	 * @return a new Array3f
	 */
	public static Array3f newInstance() {
		return new Array3f();
	}

	/**
	 * No-op: previously recycled to javolution pool. Now handled by GC.
	 */
	public static void recycle(Array3f instance) {
		// no-op: let GC handle it
	}
}
