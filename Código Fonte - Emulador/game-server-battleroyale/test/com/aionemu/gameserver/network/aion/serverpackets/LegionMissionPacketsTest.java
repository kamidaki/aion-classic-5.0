package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.LegionMissionData;
import com.aionemu.gameserver.dataholders.LegionMissionData.Activity;
import com.aionemu.gameserver.dataholders.LegionMissionData.Period;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.LegionMissionService;

/**
 * Missões da Legion contra a criação da Lost Academy (outros2 2026-09-22 10:23) e a recompensa de estágio (outros2 2026-09-22 19:22).
 */
class LegionMissionPacketsTest {

	private static final HexFormat HEX = HexFormat.of();

	private static final String OFFICIAL_MISSION_LIST = ""

		+ "9481b26a0000000003000337a53600000000000400000000000000000000000100010000000000000000000000000000000000000000000000000070"

		+ "27b26a000000007027b26a0000000000050038a5360000000000ac86010037a536000000000003050100000000000000000000000000000000000000"

		+ "0000000000007027b26a000000007027b26a000000000039a5360000000000ad86010037a53600000000000305010000000000000000000000000000"

		+ "00000000000000000000007027b26a000000007027b26a00000000003aa5360000000000ae86010037a5360000000000030501000000000000000000"

		+ "000000000000000000000000000000007027b26a000000007027b26a00000000003ba5360000000000af86010037a536000000000003060100000000"

		+ "0000000000000000000000000000000000000000007027b26a000000007027b26a00000000003ca5360000000000b386010037a53600000000000308"

		+ "01000000000000000000000000000000000000000000000000007027b26a000000007027b26a0000000000033da53600000000000500000000000000"

		+ "0000000002000100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a00000000000b003ea5360000000000cc"

		+ "8601003da536000000000003020100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a00000000003fa53600"

		+ "00000000cd8601003da536000000000003030100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a00000000"

		+ "0040a5360000000000ce8601003da536000000000003040100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa"

		+ "6a000000000041a5360000000000b88601003da536000000000003040100000000000000000000000000000000000000000000000000703eaa6a0000"

		+ "0000703eaa6a000000000042a5360000000000ba8601003da53600000000000306010000000000000000000000000000000000000000000000000070"

		+ "3eaa6a00000000703eaa6a000000000043a5360000000000cf8601003da5360000000000030501000000000000000000000000000000000000000000"

		+ "00000000703eaa6a00000000703eaa6a000000000044a5360000000000bf8601003da536000000000003030100000000000000000000000000000000"

		+ "000000000000000000703eaa6a00000000703eaa6a000000000045a5360000000000c28601003da53600000000000301010000000000000000000000"

		+ "0000000000000000000000000000703eaa6a00000000703eaa6a000000000046a5360000000000c38601003da5360000000000030801000000000000"

		+ "00000000000000000000000000000000000000703eaa6a00000000703eaa6a000000000047a5360000000000fd8601003da536000000000003020100"

		+ "000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a000000000048a5360000000000fe8601003da53600000000"

		+ "0003020100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a00000000000349a53600000000000c00000000"

		+ "0000000000000007000100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a000000000007004aa536000000"

		+ "0000d286010049a536000000000003040100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a00000000004b"

		+ "a5360000000000d386010049a536000000000003060100000000000000000000000000000000000000000000000000703eaa6a00000000703eaa6a00"

		+ "000000004ca5360000000000d486010049a536000000000003010100000000000000000000000000000000000000000000000000703eaa6a00000000"

		+ "703eaa6a00000000004da5360000000000d586010049a536000000000003020100000000000000000000000000000000000000000000000000703eaa"

		+ "6a00000000703eaa6a00000000004ea5360000000000d786010049a53600000000000302010000000000000000000000000000000000000000000000"

		+ "0000703eaa6a00000000703eaa6a00000000004fa5360000000000d986010049a5360000000000030201000000000000000000000000000000000000"

		+ "00000000000000703eaa6a00000000703eaa6a000000000050a5360000000000da86010049a536000000000003020100000000000000000000000000"

		+ "000000000000000000000000703eaa6a00000000703eaa6a0000000000";
	@Test
	void missionListMatchesLostAcademyCreation() throws Exception {
		LegionMissionData data = (LegionMissionData) JAXBContext.newInstance(LegionMissionData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/legion/legion_mission.xml"));
		Instant created = Instant.ofEpochSecond(0x6AB28194L); // 2026-09-22 13:24 UTC
		long instance = 0x36A537;
		List<SM_LEGION_MISSION_LIST.Mission> missions = new ArrayList<>();
		for (Period period : List.of(Period.DAILY, Period.WEEKLY, Period.RETURN)) {
			for (LegionMissionData.Mission mission : data.getMissions(period, Race.ASMODIANS, Activity.NONE)) {
				long start = LegionMissionService.periodStart(period, created);
				long missionInstance = instance++;
				List<SM_LEGION_MISSION_LIST.Action> actions = new ArrayList<>();
				for (int actionId : mission.getActionIds())
					actions.add(new SM_LEGION_MISSION_LIST.Action(instance++, actionId, data.getAction(actionId).getCode(), false, 0, start));
				missions.add(new SM_LEGION_MISSION_LIST.Mission(missionInstance, mission.getId(), LegionMissionService.periodCode(period), start, start, actions));
			}
		}
		assertEquals(List.of(4, 5, 12), missions.stream().map(SM_LEGION_MISSION_LIST.Mission::missionId).toList());
		assertEquals(OFFICIAL_MISSION_LIST, HEX.formatHex(body(new SM_LEGION_MISSION_LIST((int) created.getEpochSecond(), missions))));
	}

	@Test
	void updatesMatchOfficial() throws Exception {
		// Lost Academy 22/09: segunda ação da diária com 1 de progresso
		assertEquals("010039a536000000000001010000000000000000000000000000000000000000000000",
			HEX.formatHex(body(new SM_LEGION_MISSION_UPDATE(List.of(new SM_LEGION_MISSION_UPDATE.Entry(0x36A539, 1, 1))))));
		// ação 100014 concluída (35 de 35) e a diária com 1 ação concluída
		assertEquals("02003aa53600000000000223000000000000000000000000000000000000000000000037a536000000000001010000000000000000000000000000000000000000000000",
			HEX.formatHex(body(new SM_LEGION_MISSION_UPDATE(
				List.of(new SM_LEGION_MISSION_UPDATE.Entry(0x36A53A, 2, 35), new SM_LEGION_MISSION_UPDATE.Entry(0x36A537, 1, 1))))));
		// recompensa do estágio 1 da diária: 3000 de exp no nível 1 e 10 fragmentos
		assertEquals("01000000b80b000000000000", HEX.formatHex(body(new SM_LEGION_GROWTH(1, 3000))));
		assertEquals("00000000000000000a00000000000000", HEX.formatHex(body(new SM_LEGION_ESSENCE(0, 10))));
		assertEquals("1900000000003a641500013300300030003000000000", HEX.formatHex(body(new SM_SYSTEM_MESSAGE(1401914, "3000"))));
		assertEquals("1900000000007c6415000131003000000000", HEX.formatHex(body(new SM_SYSTEM_MESSAGE(1401980, "10"))));
	}

	@Test
	void periodsStartAtSevenUtc() {
		assertEquals(0x6AB22770L, LegionMissionService.periodStart(Period.DAILY, Instant.ofEpochSecond(0x6AB28194L))); // 22/09 07:00
		assertEquals(0x6AAA3E70L, LegionMissionService.periodStart(Period.WEEKLY, Instant.ofEpochSecond(0x6AB28194L))); // quarta 16/09 07:00
		// Org Asmo 13/09 08:05: diária de 13/09 e semanal de quarta 09/09
		long thirteenth = Instant.parse("2026-09-13T08:05:00Z").getEpochSecond();
		assertEquals(Instant.parse("2026-09-13T07:00:00Z").getEpochSecond(), LegionMissionService.periodStart(Period.DAILY, Instant.ofEpochSecond(thirteenth)));
		assertEquals(Instant.parse("2026-09-09T07:00:00Z").getEpochSecond(), LegionMissionService.periodStart(Period.RETURN, Instant.ofEpochSecond(thirteenth)));
		assertEquals(Instant.parse("2026-09-15T07:00:00Z").getEpochSecond(),
			LegionMissionService.periodStart(Period.DAILY, Instant.parse("2026-09-16T06:59:59Z")));
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(8192).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		Method method = null;
		for (Class<?> c = packet.getClass(); method == null; c = c.getSuperclass())
			method = Arrays.stream(c.getDeclaredMethods()).filter(m -> m.getName().equals("writeImpl")).findFirst().orElse(null);
		method.setAccessible(true);
		method.invoke(packet, new Object[] { (AionConnection) null });
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
