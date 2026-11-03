package com.aionemu.gameserver.model.team.legion;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.SplittableRandom;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.LegionDonationData;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.services.LegionDonationService;

/**
 * Produção de moedas da Legion contra as capturas oficiais: as dez produções do Kodra na criação da Lost Academy (outros2 2026-09-22 10:23),
 * a de Inshagle (2026-09-12) e as listas do dia de 06/09 a 28/09.
 */
class LegionDonationTest {

	private static LegionDonationData data() throws Exception {
		return (LegionDonationData) JAXBContext.newInstance(LegionDonationData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/legion/legion_donation.xml"));
	}

	@Test
	void entriesMatchCapturedProductions() throws Exception {
		LegionDonationData data = data();
		assertEquals(LocalTime.of(8, 0), data.getResetTime());
		LegionDonationData.Entry potion = data.getGroup(10).getEntry(1); // [13][D 10][D 1]: 1 poção 162000069, moedas +440
		assertEquals(162000069, potion.getItemId());
		assertEquals(1, potion.getCount());
		assertEquals(1, potion.getPoints());
		assertEquals(440, potion.getCoins());
		assertEquals(6600, data.getGroup(8).getEntry(10).getCoins()); // Inshagle: [13][D 8][D 10]
		assertNull(data.getGroup(10).getEntry(2));
	}

	@Test
	void groupsFollowLegionRace() throws Exception {
		LegionDonationData data = data();
		assertEquals(List.of(7, 8, 9, 10, 11, 12, 14, 15), data.getGroups(Race.ELYOS).stream().map(LegionDonationData.Group::getId).toList());
		assertEquals(List.of(7, 8, 9, 10, 11, 13, 14, 15), data.getGroups(Race.ASMODIANS).stream().map(LegionDonationData.Group::getId).toList());
	}

	@Test
	void boardRollsOncePerDayWithinGroupSizes() throws Exception {
		List<LegionDonationData.Group> groups = data().getGroups(Race.ASMODIANS);
		LegionDonationBoard board = new LegionDonationBoard(null, Map.of(), 0);
		LocalDate day = LocalDate.of(2026, 9, 22);
		assertTrue(board.rollTo(day, groups, new SplittableRandom(1)));
		Map<Integer, Integer> first = board.getSelection();
		assertEquals(8, first.size());
		for (LegionDonationData.Group group : groups)
			assertTrue(first.get(group.getId()) >= 1 && first.get(group.getId()) <= group.size());
		assertEquals(1, first.get(10)); // grupos de uma entrada sempre com 1, como nas 27 listas
		board.addPoints(10);
		assertFalse(board.rollTo(day, groups, new SplittableRandom(2)));
		assertEquals(first, board.getSelection());
		assertTrue(board.rollTo(day.plusDays(1), groups, new SplittableRandom(3)));
		assertEquals(0, board.getPoints());
		assertEquals(first, LegionDonationBoard.parseSelection(new LegionDonationBoard(day, first, 0).getSelectionText()));
	}

	@Test
	void progressCountsStreakAndCoins() {
		LocalDate day = LocalDate.of(2026, 9, 22);
		LegionDonationProgress kodra = new LegionDonationProgress(null, 0, 0, 0, 0, null, 0x20AD5);
		for (int i = 1; i <= 10; i++) {
			kodra.produce(day, 1, 440);
			assertEquals(i, kodra.getCountToday(day)); // S 0x158 [D i][D 1]
			assertEquals(1, kodra.getStreak(day));
		}
		assertEquals(0x20AD5 + 10 * 440, kodra.getCoins()); // S 0x165 foi de 0x20AD5 a 0x21C05
		kodra.addPoints(1); // produção para craft: S 0x156 [11][11]
		assertEquals(11, kodra.getPointsToday(day));
		assertEquals(11, kodra.getPointsTotal());

		LocalDate next = day.plusDays(1);
		assertEquals(0, kodra.getCountToday(next));
		assertEquals(1, kodra.getStreak(next)); // ontem produziu: a sequência continua visível
		kodra.produce(next, 1, 440);
		assertEquals(2, kodra.getStreak(next));

		LocalDate later = next.plusDays(3); // Chinike 13/09 -> 16/09 sem produzir: S 0x158 [0][0]
		assertEquals(0, kodra.getStreak(later));
		kodra.produce(later, 1, 440);
		assertEquals(1, kodra.getStreak(later));
	}

	@Test
	void dayTurnsAtResetTime() {
		LocalTime reset = LocalTime.of(8, 0);
		assertEquals(LocalDate.of(2026, 9, 21), LegionDonationService.today(LocalDateTime.of(2026, 9, 22, 7, 59), reset));
		assertEquals(LocalDate.of(2026, 9, 22), LegionDonationService.today(LocalDateTime.of(2026, 9, 22, 8, 0), reset));
	}
}
