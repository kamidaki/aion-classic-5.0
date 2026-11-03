package com.aionemu.gameserver.model.gameobjects.player;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.stats.calc.StatOwner;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.storybook.StorybookTemplate;

/**
 * Book of Legends de um personagem: quanto de cada item foi registrado em cada livro e os livros completos. É também o dono dos atributos dos
 * livros de fragmento completos, somados num efeito só.
 */
public final class PlayerStorybook implements StatOwner {

	private final Map<Integer, Map<Integer, Long>> registered = new LinkedHashMap<>();
	private final Set<Integer> finished = new LinkedHashSet<>();

	public synchronized long getRegistered(int storybookId, int itemId) {
		Map<Integer, Long> items = registered.get(storybookId);
		return items == null ? 0 : items.getOrDefault(itemId, 0L);
	}

	public synchronized void setRegistered(int storybookId, int itemId, long count) {
		registered.computeIfAbsent(storybookId, k -> new LinkedHashMap<>()).put(itemId, count);
	}

	/**
	 * @return livro -> item -> quantidade, na ordem em que foram registrados
	 */
	public synchronized Map<Integer, Map<Integer, Long>> getRegistered() {
		Map<Integer, Map<Integer, Long>> copy = new LinkedHashMap<>();
		registered.forEach((storybookId, items) -> copy.put(storybookId, Collections.unmodifiableMap(new LinkedHashMap<>(items))));
		return Collections.unmodifiableMap(copy);
	}

	public synchronized boolean isFinished(int storybookId) {
		return finished.contains(storybookId);
	}

	public synchronized void setFinished(int storybookId) {
		finished.add(storybookId);
	}

	public synchronized Set<Integer> getFinished() {
		return Set.copyOf(finished);
	}

	/**
	 * @return true se todo item do livro já tem a quantidade pedida
	 */
	public synchronized boolean isComplete(StorybookTemplate storybook) {
		for (Map.Entry<Integer, Long> piece : storybook.getPieces().entrySet())
			if (getRegistered(storybook.getId(), piece.getKey()) < piece.getValue())
				return false;
		return true;
	}

	/**
	 * Atributos de todos os livros completos que dão atributo.
	 */
	public synchronized List<StatFunction> getModifiers() {
		List<StatFunction> modifiers = new ArrayList<>();
		for (int storybookId : finished) {
			StorybookTemplate template = DataManager.STORYBOOK_DATA.getStorybook(storybookId);
			if (template != null && template.getModifiers() != null)
				modifiers.addAll(template.getModifiers());
		}
		return modifiers;
	}
}
