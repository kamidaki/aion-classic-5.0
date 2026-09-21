package com.aionemu.gameserver.services.player;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.util.List;

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
	void recordsComeBackOneByOne() {
		PlayerMoros moros = new PlayerMoros(1, 0, List.of());
		assertEquals(20, moros.getRecords(MorosService.MAX_RECORDS));
		moros.useRecords(1, 1_000);
		moros.useRecords(2, 2_000);
		assertEquals(17, moros.getRecords(MorosService.MAX_RECORDS));
		assertEquals(1_000, moros.getNextRestoreTime());
		assertEquals(1, moros.restore(1_500));
		assertEquals(18, moros.getRecords(MorosService.MAX_RECORDS));
		assertEquals(2, moros.restore(2_000));
		assertEquals(0, moros.getNextRestoreTime());
		assertEquals(20, moros.getRecords(MorosService.MAX_RECORDS));
	}
}
