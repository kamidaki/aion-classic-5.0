package com.aionemu.gameserver.services.instanceriftservice;

import com.aionemu.gameserver.model.instancerift.InstanceRiftLocation;
import com.aionemu.gameserver.model.instancerift.InstanceRiftStateType;



public class Rift extends RiftInstance<InstanceRiftLocation>
{
	public Rift(InstanceRiftLocation instanceRift) {
		super(instanceRift);
	}
	
	@Override
	public void startInstanceRift() {
		getInstanceRiftLocation().setActiveInstanceRift(this);
		despawn();
		spawn(InstanceRiftStateType.OPEN);
	}
	
	@Override
	public void stopInstanceRift() {
		getInstanceRiftLocation().setActiveInstanceRift(null);
		despawn();
		spawn(InstanceRiftStateType.CLOSED);
	}
}