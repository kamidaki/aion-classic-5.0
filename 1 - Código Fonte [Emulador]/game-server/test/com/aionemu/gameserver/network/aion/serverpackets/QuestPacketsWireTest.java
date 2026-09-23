package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;

/**
 * Testes automatizados do Wire Protocol das missões Classic 5.0 EU.
 * Compara diretamente os bytes gerados pelo servidor contra os pacotes capturados
 * em subida-1-60-2026-08-28.pcapng e 06_Sistemas_Novos_Poeta_5.0_2026-09-12.
 */
class QuestPacketsWireTest {

	private static final HexFormat HEX = HexFormat.of();

	@Test
	void questActionAddMatchesOfficialPcap() throws Exception {
		// PCAP subida-1-60: act=1 qid=20153 (0x4EB9) st=3 (START) step=0
		// Wire: 01 b9 4e 00 00 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 (21 bytes)
		QuestState qs = new QuestState(20153, QuestStatus.START, 0, 0, 0, null, null, null);
		SM_QUEST_ACTION packet = new SM_QUEST_ACTION(SM_QUEST_ACTION.ActionType.ADD, qs);
		assertEquals("01b94e000003000000000000000000000000000000", HEX.formatHex(body(packet)));
		assertEquals(21, body(packet).length);
	}

	@Test
	void questActionUpdateMatchesOfficialPcap() throws Exception {
		// PCAP subida-1-60: act=2 qid=20153 (0x4EB9) st=3 (START) step=1
		// Wire: 02 b9 4e 00 00 03 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 (21 bytes)
		QuestState qs = new QuestState(20153, QuestStatus.START, 1, 0, 0, null, null, null);
		SM_QUEST_ACTION packet = new SM_QUEST_ACTION(SM_QUEST_ACTION.ActionType.UPDATE, qs);
		assertEquals("02b94e000003000100000000000000000000000000", HEX.formatHex(body(packet)));
		assertEquals(21, body(packet).length);
	}

	@Test
	void questListMatchesOfficialPcapSingleQuest() throws Exception {
		// PCAP 06_Sistemas_Novos_Poeta: S_LOAD_WORKINGQUEST count=1 qid=10155 (0x27AB) st=3 step=1
		// Header: 01 00 ff ff (4 bytes)
		// Entry: ab 27 00 00 03 01 00 00 00 00 00 00 00 00 00 00 00 00 (18 bytes)
		// Total: 22 bytes
		QuestState qs = new QuestState(10155, QuestStatus.START, 1, 0, 0, null, null, null);
		SM_QUEST_LIST packet = new SM_QUEST_LIST(List.of(qs));
		byte[] data = body(packet);
		assertEquals("0100ffffab2700000301000000000000000000000000", HEX.formatHex(data));
		assertEquals(22, data.length);
	}

	@Test
	void questCompletedListMatchesOfficialPcap() throws Exception {
		// PCAP 06_Sistemas_Novos_Poeta: S_LOAD_FINISHEDQUEST count=2 (10153, 30706)
		// Header: 01 00 fe ff (4 bytes)
		// Entry 1 (10153): a9 27 00 00 01 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 (20 bytes)
		// Entry 2 (30706): f2 77 00 00 01 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 (20 bytes)
		// Total: 44 bytes
		QuestState qs1 = new QuestState(10153, QuestStatus.COMPLETE, 0, 0, 1, null, null, null);
		QuestState qs2 = new QuestState(30706, QuestStatus.COMPLETE, 0, 0, 1, null, null, null);
		SM_QUEST_COMPLETED_LIST packet = new SM_QUEST_COMPLETED_LIST(0, List.of(qs1, qs2));
		byte[] data = body(packet);
		assertEquals("0100feffa927000001000000000000000000000001000000f277000001000000000000000000000001000000", HEX.formatHex(data));
		assertEquals(44, data.length);
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(256).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		Method method = null;
		for (Class<?> c = packet.getClass(); method == null && c != null; c = c.getSuperclass()) {
			method = Arrays.stream(c.getDeclaredMethods()).filter(m -> m.getName().equals("writeImpl")).findFirst().orElse(null);
		}
		if (method != null) {
			method.setAccessible(true);
			method.invoke(packet, (AionConnection) null);
		}
		buffer.flip();
		byte[] res = new byte[buffer.remaining()];
		buffer.get(res);
		return res;
	}
}
