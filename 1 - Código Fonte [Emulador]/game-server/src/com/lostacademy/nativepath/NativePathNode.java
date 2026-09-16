package com.lostacademy.nativepath;

import java.util.Arrays;

/**
 * Representação imutável de um nó de navegação na grade nativa CryEngine.
 *
 * @author KAMIDAKI
 */
public final class NativePathNode {

	private final int id;
	private final float x;
	private final float y;
	private final float z;
	private final short gridX;
	private final short gridY;
	private final byte flags;
	private int[] neighborIds;

	public NativePathNode(int id, float x, float y, float z, short gridX, short gridY, byte flags, int[] neighborIds) {
		this.id = id;
		this.x = x;
		this.y = y;
		this.z = z;
		this.gridX = gridX;
		this.gridY = gridY;
		this.flags = flags;
		this.neighborIds = neighborIds != null ? neighborIds : new int[0];
	}

	void setNeighborIds(int[] neighborIds) {
		this.neighborIds = neighborIds != null ? neighborIds : new int[0];
	}

	public int getId() {
		return id;
	}

	public float getX() {
		return x;
	}

	public float getY() {
		return y;
	}

	public float getZ() {
		return z;
	}

	public short getGridX() {
		return gridX;
	}

	public short getGridY() {
		return gridY;
	}

	public byte getFlags() {
		return flags;
	}

	public int[] getNeighborIds() {
		return neighborIds;
	}

	public float distanceSquaredTo(float targetX, float targetY, float targetZ) {
		float dx = this.x - targetX;
		float dy = this.y - targetY;
		float dz = this.z - targetZ;
		return dx * dx + dy * dy + dz * dz;
	}

	public float distance2DSquaredTo(float targetX, float targetY) {
		float dx = this.x - targetX;
		float dy = this.y - targetY;
		return dx * dx + dy * dy;
	}

	public float distanceTo(NativePathNode other) {
		float dx = this.x - other.x;
		float dy = this.y - other.y;
		float dz = this.z - other.z;
		return (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
	}

	@Override
	public String toString() {
		return "NativePathNode{" +
			"id=" + id +
			", pos=(" + x + ", " + y + ", " + z + ")" +
			", grid=(" + gridX + ", " + gridY + ")" +
			", neighbors=" + Arrays.toString(neighborIds) +
			'}';
	}
}
