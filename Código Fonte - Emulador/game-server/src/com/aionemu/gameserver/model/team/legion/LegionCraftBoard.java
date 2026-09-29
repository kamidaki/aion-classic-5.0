package com.aionemu.gameserver.model.team.legion;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Quanto de cada componente os membros já doaram para cada receita de produção da Legion (S 0x15A).
 */
public class LegionCraftBoard {

	private final Map<Integer, Map<Integer, Long>> donatedByRecipe = new HashMap<>();

	public synchronized long getDonated(int recipeId, int itemId) {
		return donatedByRecipe.getOrDefault(recipeId, Map.of()).getOrDefault(itemId, 0L);
	}

	public synchronized void setDonated(int recipeId, Map<Integer, Long> donated) {
		donatedByRecipe.put(recipeId, new LinkedHashMap<>(donated));
	}

	public synchronized void addDonated(int recipeId, int itemId, long count) {
		donatedByRecipe.computeIfAbsent(recipeId, id -> new LinkedHashMap<>()).merge(itemId, count, Long::sum);
	}

	/**
	 * @return a doação da receita como gravada no banco: "item:quantidade" separados por vírgula
	 */
	public synchronized String getDonatedText(int recipeId) {
		return donatedByRecipe.getOrDefault(recipeId, Map.of()).entrySet().stream().map(e -> e.getKey() + ":" + e.getValue())
			.collect(Collectors.joining(","));
	}

	public static Map<Integer, Long> parseDonated(String text) {
		Map<Integer, Long> donated = new LinkedHashMap<>();
		if (text != null)
			for (String pair : text.split(",")) {
				if (pair.isBlank())
					continue;
				String[] parts = pair.trim().split(":");
				donated.put(Integer.parseInt(parts[0]), Long.parseLong(parts[1]));
			}
		return donated;
	}
}
