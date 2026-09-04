package com.aionemu.gameserver.taskmanager.tasks;

import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.ai.poll.AIQuestion;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.taskmanager.AbstractPeriodicTaskManager;
import com.aionemu.gameserver.taskmanager.FIFOSimpleExecutableQueue;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class MoveTaskManager extends AbstractPeriodicTaskManager
{
    private final Map<Integer, Creature> movingCreatures = new ConcurrentHashMap<>();
    private final TargetReachedManager targetReachedManager = new TargetReachedManager();
    private final TargetTooFarManager targetTooFarManager = new TargetTooFarManager();
	
    private MoveTaskManager() {
        super(100);
    }
	
    public void addCreature(Creature creature) {
        movingCreatures.put(creature.getObjectId(), creature);
    }
	
    public void removeCreature(Creature creature) {
        movingCreatures.remove(creature.getObjectId());
    }
	
    @Override
    public void run() {
        final List<Creature> arrivedCreatures = new ArrayList<>();
        final List<Creature> followingCreatures = new ArrayList<>();
        for (Iterator<Map.Entry<Integer, Creature>> it = movingCreatures.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<Integer, Creature> entry = it.next();
            Creature creature = entry.getValue();
            creature.getMoveController().moveToDestination();
            if (creature.getAi().poll(AIQuestion.DESTINATION_REACHED)) {
                it.remove();
                arrivedCreatures.add(creature);
            } else {
                followingCreatures.add(creature);
            }
        }
        targetReachedManager.executeAll(arrivedCreatures);
        targetTooFarManager.executeAll(followingCreatures);
    }

	
    public static MoveTaskManager getInstance() {
        return SingletonHolder.INSTANCE;
    }
	
    private final class TargetReachedManager extends FIFOSimpleExecutableQueue<Creature> {
        @Override
        protected void removeAndExecuteFirst() {
            final Creature creature = removeFirst();
            try {
                creature.getAi().onGeneralEvent(AIEventType.MOVE_ARRIVED);
            } catch (RuntimeException e) {
                //log.warn("", e);
            }
        }
    }
	
    private final class TargetTooFarManager extends FIFOSimpleExecutableQueue<Creature> {
        @Override
        protected void removeAndExecuteFirst() {
            final Creature creature = removeFirst();
            try {
                creature.getAi().onGeneralEvent(AIEventType.MOVE_VALIDATE);
            } catch (RuntimeException e) {
                //log.warn("", e);
            }
        }
    }
	
    private static final class SingletonHolder {
        private static final MoveTaskManager INSTANCE = new MoveTaskManager();
    }
}