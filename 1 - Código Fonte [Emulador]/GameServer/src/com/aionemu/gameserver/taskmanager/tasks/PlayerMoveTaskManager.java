package com.aionemu.gameserver.taskmanager.tasks;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.taskmanager.AbstractPeriodicTaskManager;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class PlayerMoveTaskManager extends AbstractPeriodicTaskManager
{
    private final Map<Integer, Creature> movingPlayers = new ConcurrentHashMap<>();
	
    private PlayerMoveTaskManager() {
        super(200);
    }
	
    public void addPlayer(Creature player) {
        this.movingPlayers.put(player.getObjectId(), player);
    }
	
    public void removePlayer(Creature player) {
        this.movingPlayers.remove(player.getObjectId());
    }
	
    @Override
    public void run() {
        for (Creature player : this.movingPlayers.values()) {
            player.getMoveController().moveToDestination();
        }
    }

	
    public static PlayerMoveTaskManager getInstance() {
        return SingletonHolder.INSTANCE;
    }
	
    private static final class SingletonHolder {
        private static final PlayerMoveTaskManager INSTANCE = new PlayerMoveTaskManager();
    }
}