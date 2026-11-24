package com.aionemu.gameserver.geoEngine.scene;

import java.nio.Buffer;
import java.nio.FloatBuffer;

import com.aionemu.gameserver.geoEngine.bounding.BoundingBox;
import com.aionemu.gameserver.geoEngine.bounding.BoundingVolume;
import com.aionemu.gameserver.geoEngine.collision.Collidable;
import com.aionemu.gameserver.geoEngine.collision.CollisionResults;
import com.aionemu.gameserver.geoEngine.collision.bih.BIHTree;
import com.aionemu.gameserver.geoEngine.math.Matrix4f;
import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.geoEngine.scene.mesh.IndexArray;

public class Mesh {

	/**
	 * The bounding volume that contains the mesh entirely. By default a BoundingBox (AABB).
	 */
	private BoundingVolume meshBound = new BoundingBox();

	private CollisionData collisionTree = null;

	private float[] vertices;
	private IndexArray indices;

	private byte materialId = 0;
	private byte collisionIntentions = 0;

	public Mesh() {
	}

	public int getTriangleCount() {
		return indices.size() / 3;
	}

	public int getVertexCount() {
		return vertices.length;
	}

	public void getTriangle(int index, Vector3f v1, Vector3f v2, Vector3f v3) {
		index *= 3;
		int vertexIndex = indices.get(index++) * 3;
		v1.x = vertices[vertexIndex++];
		v1.y = vertices[vertexIndex++];
		v1.z = vertices[vertexIndex];
		vertexIndex = indices.get(index++) * 3;
		v2.x = vertices[vertexIndex++];
		v2.y = vertices[vertexIndex++];
		v2.z = vertices[vertexIndex];
		vertexIndex = indices.get(index) * 3;
		v3.x = vertices[vertexIndex++];
		v3.y = vertices[vertexIndex++];
		v3.z = vertices[vertexIndex];
	}

	public void swapTriangles(int i1, int i2) {
		indices.swap(i1, i2);
	}

	public void createCollisionData() {
		if (collisionTree != null) {
			return;
		}
		BIHTree tree = new BIHTree(this);
		tree.construct();
		collisionTree = tree;
	}

	public int collideWith(Collidable other, Matrix4f worldMatrix, BoundingVolume worldBound, CollisionResults results) {

		if (collisionTree == null) {
			createCollisionData();
		}

		return collisionTree.collideWith(other, worldMatrix, worldBound, results);
	}

	public void setVertices(FloatBuffer vertices) {
		this.collisionTree = null;
		this.vertices = new float[vertices.limit()];
		vertices.get(this.vertices);
	}

	public void setIndices(Buffer indices) {
		this.collisionTree = null;
		this.indices = IndexArray.from(indices);
	}

	public void updateBound() {
		meshBound.computeFromPoints(FloatBuffer.wrap(vertices));
	}

	public BoundingVolume getBound() {
		return meshBound;
	}

	public void setBound(BoundingVolume modelBound) {
		meshBound = modelBound;
	}

	public void setCollisionIntentions(byte collisionIntentions) {
		this.collisionIntentions = collisionIntentions;
	}

	public void setMaterialId(byte materialId) {
		this.materialId = materialId;
	}

	public byte getCollisionIntentions() {
		return this.collisionIntentions;
	}

	public int getMaterialId() {
		return (this.materialId & 0xFF);
	}

}
