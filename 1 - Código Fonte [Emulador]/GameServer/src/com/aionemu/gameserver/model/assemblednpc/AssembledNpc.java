package com.aionemu.gameserver.model.assemblednpc;

import javolution.util.FastList;


public class AssembledNpc {

	private FastList<AssembledNpcPart> assembledParts = new FastList<AssembledNpcPart>();
	private long spawnTime = System.currentTimeMillis();
	private int routeId;
	private int mapId;

	public AssembledNpc(int routeId, int mapId, int liveTime, FastList<AssembledNpcPart> assembledParts) {
		this.assembledParts = assembledParts;
		this.routeId = routeId;
		this.mapId = mapId;
	}

	public FastList<AssembledNpcPart> getAssembledParts() {
		return assembledParts;
	}

	public int getRouteId() {
		return routeId;
	}

	public int getMapId() {
		return mapId;
	}

	public long getTimeOnMap() {
		return  System.currentTimeMillis() - spawnTime;
	}
}
