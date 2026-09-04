package com.aionemu.gameserver.taskmanager;

import com.aionemu.commons.utils.concurrent.RunnableStatsManager;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public abstract class AbstractIterativePeriodicTaskManager<T> extends AbstractPeriodicTaskManager {

	private final Set<T> startList = ConcurrentHashMap.newKeySet();
	private final Set<T> stopList = ConcurrentHashMap.newKeySet();

	private final Set<T> activeTasks = ConcurrentHashMap.newKeySet();

	protected AbstractIterativePeriodicTaskManager(int period) {
		super(period);
	}

	public boolean hasTask(T task) {
		readLock();
		try {
			if (stopList.contains(task))
				return false;

			return activeTasks.contains(task) || startList.contains(task);
		}
		finally {
			readUnlock();
		}
	}

	public void startTask(T task) {
		writeLock();
		try {
			startList.add(task);

			stopList.remove(task);
		}
		finally {
			writeUnlock();
		}
	}

	public void stopTask(T task) {
		writeLock();
		try {
			stopList.add(task);

			startList.remove(task);
		}
		finally {
			writeUnlock();
		}
	}

	@Override
	public final void run() {
		writeLock();
		try {
			activeTasks.addAll(startList);
			activeTasks.removeAll(stopList);

			startList.clear();
			stopList.clear();
		}
		finally {
			writeUnlock();
		}

		for (final T task : activeTasks) {
			final long begin = System.nanoTime();

			try {
				callTask(task);
			}
			catch (RuntimeException e) {
				log.warn("", e);
			}
			finally {
				RunnableStatsManager.handleStats(task.getClass(), getCalledMethodName(), System.nanoTime() - begin);
			}
		}
	}

	protected abstract void callTask(T task);

	protected abstract String getCalledMethodName();
}

