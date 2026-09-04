package com.aionemu.gameserver.model.instancerift;

import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.instancerift.InstanceRiftTemplate;
import com.aionemu.gameserver.services.instanceriftservice.RiftInstance;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import java.util.ArrayList;
import java.util.List;



public class InstanceRiftLocation
{
	protected int id;
	protected boolean isActive;
	protected InstanceRiftTemplate template;
	protected RiftInstance<InstanceRiftLocation> activeInstanceRift;
	protected Map<Integer, Player> players = new ConcurrentHashMap<Integer, Player>();
	private final List<VisibleObject> spawned = new ArrayList<VisibleObject>();
	
	public InstanceRiftLocation() {
	}
	
	public InstanceRiftLocation(InstanceRiftTemplate template) {
		this.template = template;
		this.id = template.getId();
	}
	
	public boolean isActive() {
		return isActive;
	}
	
	public void setActiveInstanceRift(RiftInstance<InstanceRiftLocation> instanceRift) {
		isActive = instanceRift != null;
		this.activeInstanceRift = instanceRift;
	}
	
	public RiftInstance<InstanceRiftLocation> getActiveInstanceRift() {
		return activeInstanceRift;
	}
	
	public final InstanceRiftTemplate getTemplate() {
		return template;
	}
	
	public int getId() {
		return id;
	}
	
	public List<VisibleObject> getSpawned() {
		return spawned;
	}
	
	public Map<Integer, Player> getPlayers() {
		return players;
	}
}