package com.aionemu.gameserver.model.team.legion;

import java.time.LocalDate;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.random.RandomGenerator;
import java.util.stream.Collectors;

import com.aionemu.gameserver.dataholders.LegionDonationData;

/**
 * Lista do dia e pontos de produção de uma Legion (S 0x159 e S 0x157).
 * <p>
 * Capturas oficiais (27 listas de 06/09 a 28/09): a lista é da Legion, igual em todas as sessões do dia, e só muda no primeiro acesso depois do
 * reset. PENDENTE_DE_COMPROVACAO: o índice de cada grupo é sorteado com chance igual (o client_guild_donation.xml não tem peso nem ordem, e
 * os índices vistos não seguem padrão).
 */
public class LegionDonationBoard {

	private LocalDate day;
	private Map<Integer, Integer> selection;
	private int points;

	public LegionDonationBoard(LocalDate day, Map<Integer, Integer> selection, int points) {
		this.day = day;
		this.selection = new LinkedHashMap<>(selection);
		this.points = points;
	}

	/**
	 * Começa o dia se ainda não começou: sorteia a lista dos grupos e zera os pontos.
	 *
	 * @return true se mudou (precisa gravar)
	 */
	public synchronized boolean rollTo(LocalDate today, List<LegionDonationData.Group> groups, RandomGenerator random) {
		if (today.equals(day) && !selection.isEmpty())
			return false;
		Map<Integer, Integer> newSelection = new LinkedHashMap<>();
		for (LegionDonationData.Group group : groups)
			newSelection.put(group.getId(), 1 + random.nextInt(group.size()));
		selection = newSelection;
		day = today;
		points = 0;
		return true;
	}

	public synchronized int addPoints(int amount) {
		return points += amount;
	}

	public synchronized LocalDate getDay() {
		return day;
	}

	public synchronized Map<Integer, Integer> getSelection() {
		return Collections.unmodifiableMap(new LinkedHashMap<>(selection));
	}

	public synchronized int getPoints() {
		return points;
	}

	/**
	 * @return a lista como gravada no banco: "grupo:índice" separados por vírgula
	 */
	public synchronized String getSelectionText() {
		return selection.entrySet().stream().map(e -> e.getKey() + ":" + e.getValue()).collect(Collectors.joining(","));
	}

	public static Map<Integer, Integer> parseSelection(String text) {
		Map<Integer, Integer> selection = new LinkedHashMap<>();
		if (text != null)
			for (String pair : text.split(",")) {
				if (pair.isBlank())
					continue;
				String[] parts = pair.trim().split(":");
				selection.put(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]));
			}
		return selection;
	}
}
