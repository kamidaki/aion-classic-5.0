package com.aionemu.gameserver.taskmanager.tasks;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.taskmanager.AbstractPeriodicTaskManager;

import javolution.util.FastMap;

public class PlayerMoveTaskManager extends AbstractPeriodicTaskManager
{
    private final FastMap<Integer, Creature> movingPlayers = new FastMap().shared();
	
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
        FastMap.Entry e = this.movingPlayers.head();
        FastMap.Entry mapEnd = this.movingPlayers.tail();
        while ((e = e.getNext()) != mapEnd) {
            Creature player = (Creature)e.getValue();
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