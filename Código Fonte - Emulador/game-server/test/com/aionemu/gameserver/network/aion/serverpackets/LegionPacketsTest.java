package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.sql.Timestamp;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.dataholders.LegionSettingsData;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionHistoryAction;
import com.aionemu.gameserver.model.team.legion.LegionHistoryEntry;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.model.team.legion.LegionRank;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Pacotes de Legion contra as capturas oficiais 5.0: criação da Lost Academy (outros2 2026-09-22 10:23), AinzOO (Global Auction House
 * 2026-09-11), Org Asmo (06_Sistemas_Novos 2026-09-13 e 16) e o logoff do Kamidakii (06_Sistemas_Novos 2026-09-22 16:14).
 */
class LegionPacketsTest {

	private static final HexFormat HEX = HexFormat.of();

	@Test
	void guildInfoOfNewLegion() throws Exception {
		Legion legion = new Legion(0x2E003817, "Lost Academy");
		assertEquals("4c006f00730074002000410063006100640065006d0079000000" + "01" + "00000000" + "0c7e081c00180008" + "00000000000000000000000000000000"
			+ "0000" + "0000" + "0000000000000000000000" + "01000000" + "00000000" + "000000000000000000000000000000000000000000000000",
			HEX.formatHex(body(new SM_LEGION_INFO(legion, 0))));

		// primeiro aviso: "Teste" às 0x6ab281f6; o último D (0 -> 10 na captura) continua PENDENTE_DE_COMPROVACAO
		legion.setAnnouncement(new Legion.Announcement("Teste", new Timestamp(0x6ab281f6L * 1000)));
		String official = "4c006f00730074002000410063006100640065006d007900000001000000000c7e081c0018000800000000000000000000000000000000540065007300740065000000"
			+ "f681b26a000000000000000000000000000000010000000000000000000000000000000000000000000000000000000a000000";
		String ours = HEX.formatHex(body(new SM_LEGION_INFO(legion, 0)));
		assertEquals(official.length(), ours.length());
		assertEquals(official.substring(0, official.length() - 8), ours.substring(0, ours.length() - 8));
	}

	@Test
	void contributionIsAnInt() throws Exception {
		Legion legion = new Legion(1, "Org Asmo");
		legion.setContributionPoints(0x0DF6CF25L);
		assertEquals("0325cff60d", HEX.formatHex(body(new SM_LEGION_EDIT(0x03, legion))));
	}

	@Test
	void memberListMatchesOfficialEntries() throws Exception {
		NetworkConfig.GAMESERVER_ID = 23;
		Legion legion = new Legion(1, "AinzOO");
		LegionMember durak = member(legion, 0x2E0F3384, "Durak", PlayerClass.GLADIATOR, 60, LegionRank.BRIGADE_GENERAL, 110010000, true, 0);
		assertEquals("01ffff84330f2e44007500720061006b000000013c00000000909e8e06010000000000000000170000000000000000000000",
			HEX.formatHex(body(new SM_LEGION_MEMBERLIST(List.of(durak), true, true))));

		LegionMember ahlirom = member(legion, 0x2E23861A, "Ahlirom", PlayerClass.RANGER, 46, LegionRank.VOLUNTEER, 120030000,
			false, 0x6882D0D4);
		assertEquals("01" + "ffff" + "1a86232e410068006c00690072006f006d000000052e00000004308327070000000000d4d08268000000000000000000000000",
			HEX.formatHex(body(new SM_LEGION_MEMBERLIST(List.of(ahlirom), true, true))));

		assertEquals("010000", HEX.formatHex(body(new SM_LEGION_MEMBERLIST(List.of(), true, true)))); // criação: lista vazia
	}

	@Test
	void memberUpdateMatchesOfficial() throws Exception {
		NetworkConfig.GAMESERVER_ID = 23;
		LegionMember durak = member(new Legion(1, "AinzOO"), 0x2E0F3384, "Durak", PlayerClass.GLADIATOR, 60, LegionRank.BRIGADE_GENERAL, 110010000,
			true, 0);
		assertEquals("84330f2e00013c909e8e06010000000017000000000000000000", HEX.formatHex(body(new SM_LEGION_UPDATE_MEMBER(durak))));
	}

	@Test
	void logoutUsesDeleteMemberWithMemberFlag() throws Exception {
		LegionMember kamidakii = member(new Legion(1, "Lost Academy"), 0x2E462BD7, "Kamidakii", PlayerClass.WARRIOR, 62, LegionRank.DEPUTY, 0,
			false, 0x6AB2D865);
		assertEquals("d72b462e0165d8b26a0000000000000000", HEX.formatHex(body(SM_LEGION_LEAVE_MEMBER.logout(kamidakii))));
	}

	@Test
	void historyEntryHas140Bytes() throws Exception {
		List<LegionHistoryEntry> entries = List.of(new LegionHistoryEntry(1, 0x6AB28194, LegionHistoryAction.CREATE, "", ""));
		byte[] body = body(new SM_LEGION_HISTORY(entries, LegionHistoryAction.Type.LEGION));
		assertEquals(12 + 140 + 2, body.length); // criação da Lost Academy: 574 b com 4 entradas
		assertEquals("010000000000000001000000" + "9481b26a" + "00", HEX.formatHex(Arrays.copyOf(body, 17)));
		assertEquals("0000", HEX.formatHex(Arrays.copyOfRange(body, body.length - 2, body.length)));
	}

	@Test
	void levelsComeFromClientGuildSetting() throws Exception {
		LegionSettingsData data = (LegionSettingsData) JAXBContext.newInstance(LegionSettingsData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/legion/legion_settings.xml"));
		assertEquals(5, data.getMaxLevel());
		assertEquals(10000, data.getLevel(1).getKinah()); // criação
		assertEquals(24, data.getLevel(1).getMaxMembers());
		assertEquals(10, data.getLevel(2).getRequiredMembers());
		assertEquals(25000000, data.getLevel(5).getKinah());
		assertEquals(72, data.getLevel(5).getMaxMembers()); // Org Asmo, nível 5, com 38 membros
		assertEquals(56, data.getLevel(5).getWarehouseSlots());
		assertNull(data.getLevel(6));
	}

	private static LegionMember member(Legion legion, int objectId, String name, PlayerClass playerClass, int level, LegionRank rank, int worldId,
		boolean online, int lastOnline) throws Exception {
		LegionMember member = new LegionMember(objectId, legion);
		member.setRank(rank);
		set(member, "name", name);
		set(member, "playerClass", playerClass);
		set(member, "level", level);
		set(member, "worldId", worldId);
		set(member, "online", online);
		set(member, "lastOnlineEpochSeconds", lastOnline);
		return member;
	}

	private static void set(Object target, String field, Object value) throws Exception {
		Field f = target.getClass().getDeclaredField(field);
		f.setAccessible(true);
		f.set(target, value);
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
