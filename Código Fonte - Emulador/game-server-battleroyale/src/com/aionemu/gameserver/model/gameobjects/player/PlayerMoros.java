package com.aionemu.gameserver.model.gameobjects.player;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Estado do Moreth, Chronicle of Time de um personagem: o nível, os pontos dentro do nível e a hora em que cada registro gasto volta.
 * <p>
 * Cada registro gasto volta sozinho depois de {@code MorosService.RESTORE_MILLIS}: na captura do Book of Legends o registro gasto às 18:26:21 voltou
 * às 18:56:27, e o personagem que estava com 0 às 02:57 tinha 20 às 08:44.
 */
public final class PlayerMoros {

	private int level;
	private long points;
	private final List<Long> restoreTimes = new ArrayList<>();

	public PlayerMoros(int level, long points, List<Long> restoreTimes) {
		this.level = level;
		this.points = points;
		this.restoreTimes.addAll(restoreTimes);
		Collections.sort(this.restoreTimes);
	}

	public synchronized int getLevel() {
		return level;
	}

	public synchronized long getPoints() {
		return points;
	}

	public synchronized void setLevelAndPoints(int level, long points) {
		this.level = level;
		this.points = points;
	}

	/**
	 * @return registros disponíveis de {@code maxRecords}
	 */
	public synchronized int getRecords(int maxRecords) {
		return Math.max(0, maxRecords - restoreTimes.size());
	}

	/**
	 * Gasta {@code count} registros, enfileirando cada um para voltar de forma sequencial
	 * a cada {@code restoreDelay} (1 ponto a cada 30 minutos).
	 */
	public synchronized void useRecords(int count, long now, long restoreDelay) {
		long lastTime = restoreTimes.isEmpty() ? now : Math.max(now, restoreTimes.getLast());
		for (int i = 0; i < count; i++) {
			lastTime += restoreDelay;
			restoreTimes.add(lastTime);
		}
		Collections.sort(restoreTimes);
	}

	@Deprecated
	public synchronized void useRecords(int count, long restoreAt) {
		for (int i = 0; i < count; i++)
			restoreTimes.add(restoreAt);
		Collections.sort(restoreTimes);
	}

	/**
	 * Garante que os registros pendentes estejam espaçados de 1 em 1 por {@code restoreDelay}
	 * (corrige dados legados no banco que possam ter gravado o mesmo timestamp para multiplos registros).
	 */
	public synchronized void normalizeRestoreTimes(long now, long restoreDelay) {
		if (restoreTimes.isEmpty())
			return;
		Collections.sort(restoreTimes);
		long nextValidTime = now;
		for (int i = 0; i < restoreTimes.size(); i++) {
			long t = restoreTimes.get(i);
			if (t <= now) {
				continue;
			}
			if (t < nextValidTime) {
				t = nextValidTime;
				restoreTimes.set(i, t);
			}
			nextValidTime = t + restoreDelay;
		}
	}

	/**
	 * Devolve os registros cujo prazo já passou.
	 *
	 * @return quantos voltaram
	 */
	public synchronized int restore(long now) {
		int restored = 0;
		while (!restoreTimes.isEmpty() && restoreTimes.getFirst() <= now) {
			restoreTimes.removeFirst();
			restored++;
		}
		return restored;
	}

	/**
	 * @return a hora do próximo registro a voltar, ou 0 se nenhum está pendente
	 */
	public synchronized long getNextRestoreTime() {
		return restoreTimes.isEmpty() ? 0 : restoreTimes.getFirst();
	}

	public synchronized List<Long> getRestoreTimes() {
		return List.copyOf(restoreTimes);
	}
}
