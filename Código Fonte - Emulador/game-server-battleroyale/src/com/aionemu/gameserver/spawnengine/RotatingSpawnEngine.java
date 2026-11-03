package com.aionemu.gameserver.spawnengine;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ScheduledFuture;
import java.util.function.Consumer;
import java.util.function.IntFunction;
import java.util.function.IntUnaryOperator;

import org.slf4j.LoggerFactory;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.templates.spawns.SpawnGroup;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.WorldMapInstance;

/** Rotação de um único NPC entre os pontos cadastrados, sem respawn independente. */
public final class RotatingSpawnEngine {

	private record Key(WorldMapInstance instance, SpawnGroup group) {}
	private record Active(Cycle<VisibleObject> cycle, ScheduledFuture<?> task) {}
	private static final Map<Key, Active> active = new HashMap<>();

	public static synchronized void start(SpawnGroup group, WorldMapInstance instance) {
		Key key = new Key(instance, group);
		if (active.containsKey(key))
			return;
		if (group.getPool() != 1 || group.getRespawnTime() != 0 || group.isTemporarySpawn()
			|| group.getSpawnTemplates().size() < 2)
			throw new IllegalArgumentException("Rotação exige pool=1, respawn_time=0 e pelo menos dois pontos: " + group.getNpcId());
		List<com.aionemu.gameserver.model.templates.spawns.SpawnTemplate> spots = List.copyOf(group.getSpawnTemplates());
		Cycle<VisibleObject> cycle = new Cycle<>(spots.size(), Rnd::nextInt,
			i -> SpawnEngine.spawnObject(spots.get(i), instance.getInstanceId()),
			object -> {
				object.getController().delete();
				com.aionemu.gameserver.services.RespawnService.cancelRespawn(object);
			});
		Runnable rotate = () -> {
			try {
				cycle.rotate();
			} catch (RuntimeException e) {
				LoggerFactory.getLogger(RotatingSpawnEngine.class).error("Falha na rotação do NPC " + group.getNpcId(), e);
			}
		};
		rotate.run();
		long period = group.getRotationTime() * 1000L;
		active.put(key, new Active(cycle, ThreadPoolManager.getInstance().scheduleAtFixedRate(rotate, period, period)));
	}

	public static synchronized void onInstanceDestroy(WorldMapInstance instance) {
		active.entrySet().removeIf(entry -> {
			if (entry.getKey().instance() != instance)
				return false;
			entry.getValue().task().cancel(false);
			entry.getValue().cycle().close();
			return true;
		});
	}

	/** Estado serializado para impedir sobreposição entre troca de ponto e encerramento. */
	static final class Cycle<T> {
		private final int spots;
		private final IntUnaryOperator random;
		private final IntFunction<T> spawn;
		private final Consumer<T> delete;
		private T current;
		private int previous = -1;
		private boolean closed;

		Cycle(int spots, IntUnaryOperator random, IntFunction<T> spawn, Consumer<T> delete) {
			if (spots < 2)
				throw new IllegalArgumentException("São necessários pelo menos dois pontos");
			this.spots = spots;
			this.random = random;
			this.spawn = spawn;
			this.delete = delete;
		}

		synchronized void rotate() {
			if (closed)
				return;
			int next = random.applyAsInt(previous < 0 ? spots : spots - 1);
			if (previous >= 0 && next >= previous)
				next++;
			if (current != null) {
				delete.accept(current);
				current = null;
			}
			current = spawn.apply(next);
			if (current != null)
				previous = next;
		}

		synchronized void close() {
			closed = true;
			if (current != null) {
				delete.accept(current);
				current = null;
			}
		}
	}
}
