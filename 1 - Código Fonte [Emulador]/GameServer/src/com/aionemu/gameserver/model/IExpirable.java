package com.aionemu.gameserver.model;

import com.aionemu.gameserver.model.gameobjects.player.Player;


public interface IExpirable {

	public int getExpireTime();

	public void expireEnd(Player player);

	public boolean canExpireNow();

	public void expireMessage(Player player, int time);
}
