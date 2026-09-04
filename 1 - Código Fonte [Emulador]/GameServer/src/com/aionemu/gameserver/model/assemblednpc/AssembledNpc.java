package com.aionemu.gameserver.model.assemblednpc;

import java.util.List;
import java.util.ArrayList;


public class AssembledNpc {

	private List<AssembledNpcPart> assembledParts = new ArrayList<AssembledNpcPart>();
	private long spawnTime = System.currentTimeMillis();
	private int routeId;
	private int mapId;

	public AssembledNpc(int routeId, int mapId, int liveTime, List<AssembledNpcPart> assembledParts) {
		this.assembledParts = assembledParts;
		this.routeId = routeId;
		this.mapId = mapId;
	}

	public List<AssembledNpcPart> getAssembledParts() {
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
