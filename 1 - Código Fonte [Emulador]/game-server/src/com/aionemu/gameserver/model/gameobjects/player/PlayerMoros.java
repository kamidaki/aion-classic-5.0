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
	 * Gasta {@code count} registros, que voltam em {@code restoreAt}.
	 */
	public synchronized void useRecords(int count, long restoreAt) {
		for (int i = 0; i < count; i++)
			restoreTimes.add(restoreAt);
		Collections.sort(restoreTimes);
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
