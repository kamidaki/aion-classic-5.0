package com.aionemu.gameserver.services.player;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.util.List;
import java.util.Map;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.MorosData;
import com.aionemu.gameserver.model.gameobjects.player.PlayerMoros;

/**
 * Pontos e níveis do Moreth sobre o moros/moros.xml, e os registros que voltam.
 */
class MorosServiceTest {

	private MorosData previous;

	@BeforeEach
	void loadData() throws Exception {
		previous = DataManager.MOROS_DATA;
		DataManager.MOROS_DATA = (MorosData) JAXBContext.newInstance(MorosData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/moros/moros.xml"));
	}

	@AfterEach
	void restoreData() {
		DataManager.MOROS_DATA = previous;
	}

	@Test
	void pointsCarryOverAndStopAtMaxLevel() {
		PlayerMoros moros = new PlayerMoros(1, 1281, List.of());
		MorosService.addPoints(moros, 2); // captura: 1281 -> 1283 no nível 1
		assertEquals(1, moros.getLevel());
		assertEquals(1283, moros.getPoints());

		moros = new PlayerMoros(1, 8000, List.of());
		MorosService.addPoints(moros, 2000); // passa dos 8850 do nível 2 e sobra 1150
		assertEquals(2, moros.getLevel());
		assertEquals(1150, moros.getPoints());

		MorosService.addPoints(moros, 1_000_000); // sobe até o 10 e para
		assertEquals(10, moros.getLevel());
		assertEquals(0, moros.getPoints());
	}

	@Test
	void everyRecordedUnitCostsOneRecord() {
		// janela do cliente em 29/09: uma pilha de 20 previa "0 + 20/20", e o cliente limita o que se põe aos registros disponíveis
		assertEquals(20, MorosService.totalUnits(Map.of(0xC04083FE, 20L)));
		assertEquals(23, MorosService.totalUnits(Map.of(1, 20L, 2, 3L)));
		assertEquals(1, MorosService.totalUnits(Map.of(1, 1L)));

		PlayerMoros moros = new PlayerMoros(1, 0, List.of());
		moros.useRecords((int) MorosService.totalUnits(Map.of(0xC04083FE, 20L)), 0, 1_000);
		assertEquals(0, moros.getRecords(MorosService.MAX_RECORDS), "a pilha de 20 gasta os 20 registros, não 1");
		assertEquals(1, moros.restore(1_000), "o 1o registro volta no 1o intervalo de tempo");
		assertEquals(1, moros.getRecords(MorosService.MAX_RECORDS));
		assertEquals(19, moros.restore(20_000), "os outros voltam sequencialmente a cada intervalo");
		assertEquals(20, moros.getRecords(MorosService.MAX_RECORDS));
	}

	@Test
	void recordsComeBackOneByOne() {
		PlayerMoros moros = new PlayerMoros(1, 0, List.of());
		assertEquals(20, moros.getRecords(MorosService.MAX_RECORDS));
		moros.useRecords(1, 0, 1_000); // agendado para 1_000
		moros.useRecords(2, 500, 1_000); // agendados para 2_000 e 3_000
		assertEquals(17, moros.getRecords(MorosService.MAX_RECORDS));
		assertEquals(1_000, moros.getNextRestoreTime());
		assertEquals(1, moros.restore(1_500));
		assertEquals(18, moros.getRecords(MorosService.MAX_RECORDS));
		assertEquals(2_000, moros.getNextRestoreTime());
		assertEquals(1, moros.restore(2_000));
		assertEquals(19, moros.getRecords(MorosService.MAX_RECORDS));
		assertEquals(3_000, moros.getNextRestoreTime());
		assertEquals(1, moros.restore(3_000));
		assertEquals(0, moros.getNextRestoreTime());
		assertEquals(20, moros.getRecords(MorosService.MAX_RECORDS));
	}

	@Test
	void normalizeLegacyIdenticalTimestamps() {
		PlayerMoros moros = new PlayerMoros(1, 0, List.of(10_000L, 10_000L, 10_000L));
		moros.normalizeRestoreTimes(5_000L, 1_000L);
		List<Long> times = moros.getRestoreTimes();
		assertEquals(List.of(10_000L, 11_000L, 12_000L), times);
	}
}
