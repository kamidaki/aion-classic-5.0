package com.aionemu.gameserver.model.team.legion;

import java.time.LocalDate;

/**
 * Produção de moedas de um personagem: contadores do dia, total, dias seguidos e saldo de moedas pessoais da Legion.
 * <p>
 * Capturas oficiais: S 0x158 [D produções hoje][D dias seguidos] (Kodra 1..10 com 1 no primeiro dia; o Chinike tinha 1 dia em 13/09 e voltou a 0
 * em 16/09 depois de ficar 3 dias sem produzir), S 0x156 [D pontos hoje][D pontos total] (a produção para craft também soma), S 0x165 [D moedas].
 * O texto do cliente confirma: a sequência só avança com ao menos uma produção no dia (STR_DLG_GUILD_DONATION_MY_TIP).
 */
public class LegionDonationProgress {

	private LocalDate day;
	private int countToday;
	private int pointsToday;
	private int pointsTotal;
	private int streak;
	private LocalDate lastProductionDay;
	private int coins;

	public LegionDonationProgress(LocalDate day, int countToday, int pointsToday, int pointsTotal, int streak, LocalDate lastProductionDay, int coins) {
		this.day = day;
		this.countToday = countToday;
		this.pointsToday = pointsToday;
		this.pointsTotal = pointsTotal;
		this.streak = streak;
		this.lastProductionDay = lastProductionDay;
		this.coins = coins;
	}

	public static LegionDonationProgress empty() {
		return new LegionDonationProgress(null, 0, 0, 0, 0, null, 0);
	}

	/**
	 * Zera os contadores do dia se o dia virou.
	 *
	 * @return true se mudou (precisa gravar)
	 */
	public synchronized boolean rollTo(LocalDate today) {
		if (today.equals(day))
			return false;
		day = today;
		countToday = 0;
		pointsToday = 0;
		return true;
	}

	/**
	 * Registra uma produção: conta, pontos, moedas e dias seguidos (sobe no primeiro do dia se ontem houve produção, senão volta a 1).
	 */
	public synchronized void produce(LocalDate today, int points, int coinsGained) {
		rollTo(today);
		if (!today.equals(lastProductionDay))
			streak = today.minusDays(1).equals(lastProductionDay) ? streak + 1 : 1;
		lastProductionDay = today;
		countToday++;
		addPoints(points);
		coins = (int) Math.min((long) coins + coinsGained, Integer.MAX_VALUE);
	}

	public synchronized void addPoints(int points) {
		pointsToday += points;
		pointsTotal += points;
	}

	/**
	 * @return dias seguidos como o cliente mostra: 0 se ontem e hoje ficaram sem produção
	 */
	public synchronized int getStreak(LocalDate today) {
		return lastProductionDay != null && !lastProductionDay.isBefore(today.minusDays(1)) ? streak : 0;
	}

	public synchronized int getCountToday(LocalDate today) {
		return today.equals(day) ? countToday : 0;
	}

	public synchronized int getPointsToday(LocalDate today) {
		return today.equals(day) ? pointsToday : 0;
	}

	public synchronized int getPointsTotal() {
		return pointsTotal;
	}

	public synchronized int getCoins() {
		return coins;
	}

	public synchronized LocalDate getDay() {
		return day;
	}

	public synchronized int getStoredStreak() {
		return streak;
	}

	public synchronized LocalDate getLastProductionDay() {
		return lastProductionDay;
	}

	public synchronized int getStoredCountToday() {
		return countToday;
	}

	public synchronized int getStoredPointsToday() {
		return pointsToday;
	}
}
