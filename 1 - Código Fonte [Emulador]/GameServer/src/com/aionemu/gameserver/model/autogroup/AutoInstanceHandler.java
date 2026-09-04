package com.aionemu.gameserver.model.autogroup;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.world.WorldMapInstance;

public interface AutoInstanceHandler
{
	public abstract void initsialize(int instanceMaskId);
	public abstract void onInstanceCreate(WorldMapInstance instance);
	public abstract AGQuestion addPlayer(Player player, SearchInstance searchInstance);
	public abstract void onEnterInstance(Player player);
	public abstract void onLeaveInstance(Player player);
	public abstract void onPressEnter(Player player);
	public abstract void unregister(Player player);
	public abstract void clear();
}