package com.aionemu.gameserver.model.team.legion;

import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Quanto de cada componente os membros já doaram para cada receita de produção da Legion (S 0x15A).
 */
public class LegionCraftBoard {

	private final Map<Integer, Map<Integer, Long>> donatedByRecipe = new HashMap<>();
	private final Map<Integer, Integer> craftStartByRecipe = new HashMap<>();
	private final Map<Integer, Boolean> craftingByRecipe = new HashMap<>();
	private final Set<Integer> bookmarks = new HashSet<>();

	/**
	 * @return hora (s) do último início de produção da receita, 0 se nunca produziu; o S 0x15A a mostra mesmo depois de concluída (Nova Pasta
	 *         2026-09-29 16:02)
	 */
	public synchronized int getCraftStart(int recipeId) {
		return craftStartByRecipe.getOrDefault(recipeId, 0);
	}

	public synchronized boolean isCrafting(int recipeId) {
		return craftingByRecipe.getOrDefault(recipeId, false);
	}

	public synchronized void setCraft(int recipeId, int craftStart, boolean crafting) {
		craftStartByRecipe.put(recipeId, craftStart);
		craftingByRecipe.put(recipeId, crafting);
	}

	/**
	 * Começa a produção: os materiais doados são consumidos (o S 0x15A do início volta com as doações em 0).
	 */
	public synchronized void startCraft(int recipeId, int now) {
		donatedByRecipe.remove(recipeId);
		setCraft(recipeId, now, true);
	}

	public synchronized void finishCraft(int recipeId) {
		craftingByRecipe.put(recipeId, false);
	}

	/**
	 * @return receitas em produção com a hora de início
	 */
	public synchronized Map<Integer, Integer> getCrafting() {
		Map<Integer, Integer> crafting = new HashMap<>();
		craftingByRecipe.forEach((recipe, active) -> {
			if (active)
				crafting.put(recipe, craftStartByRecipe.getOrDefault(recipe, 0));
		});
		return crafting;
	}

	/**
	 * Favorito de produção, da Legion inteira: o C final da receita no S 0x15A dos logins seguintes (Nova Pasta 2026-09-29 16:40 e 16:49).
	 */
	public synchronized boolean isBookmarked(int recipeId) {
		return bookmarks.contains(recipeId);
	}

	public synchronized void setBookmarked(int recipeId, boolean bookmarked) {
		if (bookmarked)
			bookmarks.add(recipeId);
		else
			bookmarks.remove(recipeId);
	}

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
