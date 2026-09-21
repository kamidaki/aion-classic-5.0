package com.aionemu.gameserver.world.zone;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.templates.zone.ZoneInfo;

public class NoFlyZoneInstance extends ZoneInstance {

	public NoFlyZoneInstance(int mapId, ZoneInfo template) {
		super(mapId, template);
	}

	@Override
	public synchronized boolean onEnter(Creature creature) {
        return super.onEnter(creature);
    }

	@Override
	public synchronized boolean onLeave(Creature creature) {
        return super.onLeave(creature);
    }
}
