package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.Collections;
import java.util.HexFormat;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANK_LIST.RankingEntry;

/**
 * Testes dos pacotes de Ranking 5.0 (SM_RANK_LIST, SM_RANK_INFO, SM_RANKING_BADGE)
 * contra os bytes exatos capturados nos tráfegos oficiais (CombatTalent e aumentariventario).
 */
class RankingPacketsTest {

	private static final HexFormat HEX = HexFormat.of();

	@Test
	void rankBadgePacketMatchesOfficialCapture() throws Exception {
		// SM_RANKING_BADGE (0x0138) = opção "mostrar ranking badge": 1 no login de quem nunca mexeu; 0 e 1 no C 0xC8 (06_Sistemas_Novos 2026-10-20 02:17)
		assertEquals("0000000001", HEX.formatHex(body(new SM_RANKING_BADGE(true))));
		assertEquals("0000000000", HEX.formatHex(body(new SM_RANKING_BADGE(false))));
		// SM_RANKING_BADGE_OTHER (0x0139), mesma captura
		assertEquals("d95b0f2e0000000000", HEX.formatHex(body(new SM_RANKING_BADGE_OTHER(0x2E0F5BD9, false))));
		assertEquals("d95b0f2e0000000001", HEX.formatHex(body(new SM_RANKING_BADGE_OTHER(0x2E0F5BD9, true))));
	}

	@Test
	void rankInfoPacketsMatchOfficialCaptures() throws Exception {
		// CombatTalent_2026-09-19_00-07-06: jogador ranqueado na posição 53 com 14811 pontos no tipo 1001
		SM_RANK_INFO info1001 = new SM_RANK_INFO(1001, 53, 14811, 73, 13248);
		assertEquals(
			"e903000035000000db39000000000000000000000000000049000000c033000035000000db390000",
			HEX.formatHex(body(info1001))
		);

		// aumentariventario_2026-09-19_00-15-58: jogador não ranqueado no tipo 1000 com 8834 pontos, bestRank=-1
		SM_RANK_INFO info1000 = new SM_RANK_INFO(1000, 0, 8834, -1, 0);
		assertEquals(
			"e80300000000000082220000000000000000000000000000ffffffff000000000000000082220000",
			HEX.formatHex(body(info1000))
		);

		// aumentariventario_2026-09-19_00-15-58: jogador não ranqueado no tipo 1002 com 3497 pontos, bestRank=0, bestScore=3497
		SM_RANK_INFO info1002 = new SM_RANK_INFO(1002, 0, 3497, 0, 3497);
		assertEquals(
			"ea03000000000000a90d000000000000000000000000000000000000a90d000000000000a90d0000",
			HEX.formatHex(body(info1002))
		);
	}

	@Test
	void rankListHeaderAndEntriesMatchOfficialCapture() throws Exception {
		// Entradas extraídas de CombatTalent_2026-09-19_00-07-06 (tipo 1003, local por classe):
		// Entrada 0: Skyblade (Soul Reaper = 25, Elyos = 0, score = 40051, rank = 1, oldRank = 1, id = 0x2E4629EC)
		RankingEntry e0 = new RankingEntry(1003, 40051, 1, 1, 0x2E4629EC, 0, 25, "Skyblade");
		// Entrada 1: Its (Soul Reaper = 25, Asmo = 1, score = 39286, rank = 2, oldRank = 2, id = 0x2E4629E8)
		RankingEntry e1 = new RankingEntry(1003, 39286, 2, 2, 0x2E4629E8, 1, 25, "Its");

		int timestamp = 1789787222; // 0x6AADFC56
		SM_RANK_LIST listPart1 = new SM_RANK_LIST(1003, true, true, false, timestamp, List.of(e0, e1));
		byte[] bytes = body(listPart1);

		// Cabeçalho de 13 bytes esperado:
		// tipo=1003 (eb030000), local=1 (01), first=1 (01), ts=1789787222 (56fcad6a), count=2 (0200), hasEntries=1 (01)
		assertEquals("eb030000010156fcad6a020001", HEX.formatHex(Arrays.copyOfRange(bytes, 0, 13)));

		// Entrada 0 (85 bytes):
		String expectedE0 = "eb030000739c0000010000000100000000000000ec29462e000000001900000017"
			+ "53006b00790062006c00610064006500000000000000000000000000000000000000000000000000000000000000000000000000";
		assertEquals(expectedE0, HEX.formatHex(Arrays.copyOfRange(bytes, 13, 13 + 85)));

		// Entrada 1 (85 bytes):
		String expectedE1 = "eb03000076990000020000000200000000000000e829462e010000001900000017"
			+ "49007400730000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
		assertEquals(expectedE1, HEX.formatHex(Arrays.copyOfRange(bytes, 13 + 85, 13 + 170)));
		assertEquals(13 + 2 * 85, bytes.length);
	}

	@Test
	void rankListFinalChunkAndEmptyChunkFormatting() throws Exception {
		int timestamp = 1789787222;

		// No último pacote (isLastPart=true), o count deve ser serializado com sinal negativo (ex: -18 = 0xffee)
		RankingEntry e0 = new RankingEntry(1002, 52950, 1, 1, 0x2E13AFA9, 0, 4, "Tursia");
		SM_RANK_LIST lastPart = new SM_RANK_LIST(1002, true, false, true, timestamp, List.of(e0));
		byte[] lastBytes = body(lastPart);
		// count = -1 (short 0xffff)
		assertEquals("ea030000010056fcad6affff01", HEX.formatHex(Arrays.copyOfRange(lastBytes, 0, 13)));

		// Pacote vazio (lista sem participantes): count = 0, hasEntries = 0
		SM_RANK_LIST emptyPart = new SM_RANK_LIST(1000, false, true, true, timestamp, Collections.emptyList());
		byte[] emptyBytes = body(emptyPart);
		assertEquals("e8030000000156fcad6a000000", HEX.formatHex(emptyBytes));
		assertEquals(13, emptyBytes.length);
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
