package com.lostacademy.nativepath;

import java.util.Arrays;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Representação imutável de um nó macro de navegação na malha CryEngine.
 *
 * Utilizado pelo grafo macro para interconexão de setores transitáveis em travessias de longa
 * distância (retorno ao spawn, patrulhas de rotas de monstros e guardas).
 *
 * @author KAMIDAKI & Equipe Lost Academy
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

	/**
	 * Construtor do nó de navegação.
	 *
	 * @param id          Identificador único do nó na malha.
	 * @param x           Coordenada X em metros.
	 * @param y           Coordenada Y em metros.
	 * @param z           Coordenada Z em metros.
	 * @param gridX       Coordenada discreta de grade X.
	 * @param gridY       Coordenada discreta de grade Y.
	 * @param flags       Sinalizadores de transitabilidade CryEngine.
	 * @param neighborIds Identificadores dos nós vizinhos conectados.
	 */
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

	/**
	 * Distância euclidiana tridimensional ao quadrado até a coordenada alvo.
	 */
	public float distanceSquaredTo(float targetX, float targetY, float targetZ) {
		float dx = this.x - targetX;
		float dy = this.y - targetY;
		float dz = this.z - targetZ;
		return dx * dx + dy * dy + dz * dz;
	}

	/**
	 * Distância euclidiana bidimensional plana ao quadrado até a coordenada alvo.
	 */
	public float distance2DSquaredTo(float targetX, float targetY) {
		float dx = this.x - targetX;
		float dy = this.y - targetY;
		return dx * dx + dy * dy;
	}

	/**
	 * Distância euclidiana tridimensional até outro nó de navegação.
	 */
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
