package com.aionemu.gameserver.taskmanager.tasks;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.taskmanager.AbstractPeriodicTaskManager;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;

import java.util.Collection;
import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class TemporaryTradeTimeTask extends AbstractPeriodicTaskManager
{
	private final Map<Item, Collection<Integer>> items = new ConcurrentHashMap<>();
	private final Map<Integer, Item> itemById = new ConcurrentHashMap<>();
	
	public TemporaryTradeTimeTask() {
		super(1000);
	}
	
	public static TemporaryTradeTimeTask getInstance() {
		return SingletonHolder._instance;
	}
	
	public void addTask(Item item, Collection<Integer> players) {
		writeLock();
		try {
			items.put(item, players);
			itemById.put(item.getObjectId(), item);
		} finally {
			writeUnlock();
		}
	}

	public boolean canTrade(Item item, int playerObjectId) {
		Collection<Integer> players = items.get(item);
		if (players == null)
			return false;
		return players.contains(playerObjectId);
	}

	public boolean hasItem(Item item) {
		readLock();
		try {
			return items.containsKey(item);
		} finally {
			readUnlock();
		}
	}

	public Item getItem(int objectId) {
		readLock();
		try {
			return itemById.get(objectId);
		} finally {
			readUnlock();
		}
	}
	
	@Override
	public void run() {
		writeLock();
		try {
			for (Iterator<Map.Entry<Item, Collection<Integer>>> it = items.entrySet().iterator(); it.hasNext(); ) {
				Map.Entry<Item, Collection<Integer>> entry = it.next();
				Item item = entry.getKey();
				int time = (item.getTemporaryExchangeTime() - (int) (System.currentTimeMillis() / 1000));
				if (time == 60) {
					for (int playerId : entry.getValue()) {
						Player player = World.getInstance().findPlayer(playerId);
						if (player != null) {
							///%0's temporary trade time has expired. %0 can no longer be traded.
							PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_MSG_END_OF_EXCHANGE_TIME(item.getNameId(), time));
						}
					}
				} else if (time <= 0) {
					for (int playerId : entry.getValue()) {
						Player player = World.getInstance().findPlayer(playerId);
						if (player != null) {
							///%0's temporary trade time has expired and can no longer be traded.
							PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_MSG_EXCHANGE_TIME_OVER(item.getNameId()));
						}
					}
					item.setTemporaryExchangeTime(0);
					it.remove();
					itemById.remove(item.getObjectId());
				}
			}
		} finally {
			writeUnlock();
		}
	}

	
	@SuppressWarnings("synthetic-access")
	private static class SingletonHolder {
		protected static final TemporaryTradeTimeTask _instance = new TemporaryTradeTimeTask();
	}
}