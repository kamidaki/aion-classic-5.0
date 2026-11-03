package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.sql.Timestamp;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.dataholders.LegionCraftData;
import com.aionemu.gameserver.dataholders.LegionSettingsData;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionApplicant;
import com.aionemu.gameserver.model.team.legion.LegionHistoryAction;
import com.aionemu.gameserver.model.team.legion.LegionHistoryEntry;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.model.team.legion.LegionPermissionsMask;
import com.aionemu.gameserver.model.team.legion.LegionRank;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Pacotes de Legion contra as capturas oficiais 5.0: criação da Lost Academy (outros2 2026-09-22 10:23), AinzOO (Global Auction House
 * 2026-09-11), Org Asmo (06_Sistemas_Novos 2026-09-13 e 16) e o logoff do Kamidakii (06_Sistemas_Novos 2026-09-22 16:14).
 */
class LegionPacketsTest {

	private static final HexFormat HEX = HexFormat.of();

	private static final String OFFICIAL_CRAFT_LIST = ""
		+ "28000100000000000000000000000000000200000000000000000000000000000300000000000000000000000000000d000000000000000000000001"
		+ "000134df0a00000000000e000000000000000000000001000134df0a00000000000f000000000000000000000001000134df0a000000000010000000"
		+ "000000000000000001000134df0a000000000011000000000000000000000001000134df0a000000000012000000000000000000000001000134df0a"
		+ "000000000013000000000000000000000001000134df0a000000000018000000000000000000000001000134df0a0000000000190000000000000000"
		+ "00000001000134df0a00000000001a000000000000000000000001000134df0a00000000001b000000000000000000000001000134df0a0000000000"
		+ "660000000000000000000000040086590f09000000001db80f09000000001eb80f09000000000bd7180a000000000067000000000000000000000004"
		+ "0088590f090000000021b80f090000000022b80f09000000000cd7180a0000000000c9000000000000000000000006003bc80f09000000003cc80f09"
		+ "000000003dc80f09000000003ec80f09000000003fc80f090000000040c80f0900000000002c010000000000000000000001000134df0a0000000000"
		+ "2d010000000000000000000002000134df0a000000003823160b00000000002e010000000000000000000002000134df0a000000003823160b000000"
		+ "00002f010000000000000000000002000134df0a000000003823160b000000000030010000000000000000000002000134df0a000000003823160b00"
		+ "0000000031010000000000000000000002000134df0a000000003823160b000000000032010000000000000000000002000134df0a00000000382316"
		+ "0b000000000033010000000000000000000002000134df0a000000003823160b000000000034010000000000000000000002000134df0a0000000038"
		+ "23160b000000000090010000000000000000000001000134df0a000000000091010000000000000000000001000134df0a0000000000920100000000"
		+ "00000000000001000134df0a000000000093010000000000000000000001000134df0a000000000094010000000000000000000001000134df0a0000"
		+ "00000095010000000000000000000001000134df0a000000000097010000000000000000000001000134df0a00000000009801000000000000000000"
		+ "0001000134df0a000000000099010000000000000000000001000134df0a0000000000f5010000000000000000000002000134df0a00000000e87116"
		+ "0b0000000000f7010000000000000000000001004023160b0000000000f801000000000000000000000100f871160b0000000000fa01000000000000"
		+ "0000000001003c72160b0000000000fb010000000000000000000001003c72160b000000000001";

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
			HEX.formatHex(body(new SM_LEGION_MEMBERLIST(List.of(durak), true, true, new int[][] { { 0, 0 } }))));

		LegionMember ahlirom = member(legion, 0x2E23861A, "Ahlirom", PlayerClass.RANGER, 46, LegionRank.VOLUNTEER, 120030000,
			false, 0x6882D0D4);
		assertEquals("01" + "ffff" + "1a86232e410068006c00690072006f006d000000052e00000004308327070000000000d4d08268000000000000000000000000",
			HEX.formatHex(body(new SM_LEGION_MEMBERLIST(List.of(ahlirom), true, true, new int[][] { { 0, 0 } }))));

		// Org Asmo 16/09: Adnama offline com 0 pontos hoje e 61 no total (os mesmos do S 0x156)
		LegionMember adnama = member(new Legion(2, "Org Asmo"), 0x2E0F59D3, "Adnama", PlayerClass.CLERIC, 60, LegionRank.VOLUNTEER, 220070000,
			false, 0x686AFD48);
		assertEquals("01ffff" + "d3590f2e410064006e0061006d00610000000a3c0000000470001e0d000000000048fd6a6800000000000000003d000000",
			HEX.formatHex(body(new SM_LEGION_MEMBERLIST(List.of(adnama), true, true, new int[][] { { 0, 61 } }))));

		assertEquals("010000", HEX.formatHex(body(new SM_LEGION_MEMBERLIST(List.of(), true, true, new int[0][])))); // criação: lista vazia
	}

	@Test
	void craftListMatchesLostAcademyCreation() throws Exception {
		LegionCraftData data = (LegionCraftData) JAXBContext.newInstance(LegionCraftData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/legion/legion_craft.xml"));
		List<SM_LEGION_CRAFT_LIST.Recipe> recipes = new ArrayList<>();
		for (LegionCraftData.Recipe recipe : data.getRecipes(Race.ASMODIANS))
			recipes.add(new SM_LEGION_CRAFT_LIST.Recipe(recipe.getId(),
				recipe.getDonatableComponents().stream().map(c -> new SM_LEGION_CRAFT_LIST.Component(c.getItemId(), 0)).toList()));
		// criação da Lost Academy (asmodiana): as 40 receitas ativas de raça all + dark, sem doação, 1059 b
		assertEquals(OFFICIAL_CRAFT_LIST, HEX.formatHex(body(new SM_LEGION_CRAFT_LIST(recipes))));
		// doação do Kodra para a 501: 1 kinah e 1 classic_iddramata_01_essence
		assertEquals("0100f5010000000000000000000002000134df0a01000000e871160b010000000001",
			HEX.formatHex(body(new SM_LEGION_CRAFT_LIST(List.of(new SM_LEGION_CRAFT_LIST.Recipe(501,
				List.of(new SM_LEGION_CRAFT_LIST.Component(182400001, 1), new SM_LEGION_CRAFT_LIST.Component(186020328, 1))))))));
	}

	@Test
	void essenceProductionMatchesLostAcademy() throws Exception {
		LegionCraftData data = (LegionCraftData) JAXBContext.newInstance(LegionCraftData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/legion/legion_craft.xml"));
		LegionCraftData.Recipe essence = data.getRecipe(1);
		assertTrue(essence.isEssenceRecipe());
		assertEquals(10, essence.getEssencePieceCost());
		assertEquals(1, essence.getEssenceCount());
		assertTrue(data.getRecipe(3).isEssenceRecipe());
		assertFalse(data.getRecipe(501).isEssenceRecipe());
		// outros2 2026-09-22 19:22: C_GUILD [15][D 1] -> fragmentos 10 -> 0, receita 1 com a hora de início, essência 0 -> 1
		assertEquals("00000000000000000000000000000000", HEX.formatHex(body(new SM_LEGION_ESSENCE(0, 0))));
		assertEquals("010001000000ccffb26a0000000000000001",
			HEX.formatHex(body(new SM_LEGION_CRAFT_LIST(List.of(new SM_LEGION_CRAFT_LIST.Recipe(1, 0x6AB2FFCC, List.of()))))));
		assertEquals("01000000000000000000000000000000", HEX.formatHex(body(new SM_LEGION_ESSENCE(1, 0))));
	}

	@Test
	void permissionsAndBookmarkMatchNovaPasta() throws Exception {
		// Nova Pasta 2026-09-29 16:14: C_GUILD 0x0D devolvido no S 0x9D 02 e o favorito da receita 1 no S 0x167
		Legion legion = new Legion(1, "Lost Academy");
		legion.setLegionPermissions((short) 0x7E1C, (short) 0x1C08, (short) 0x1800, (short) 0x0800);
		assertEquals("02" + "1c7e081c00180008", HEX.formatHex(body(new SM_LEGION_EDIT(0x02, legion))));
		assertEquals("0100000001", HEX.formatHex(body(new SM_LEGION_CRAFT_BOOKMARK(1, true))));
		// Legion Join Settings (16:40: forma 2 sem texto e depois "Teste") e Legion Activity (campanha 2, Friendship e Freedom)
		legion.setJoinSettings(2, 0, "");
		assertEquals("0b0000020000", HEX.formatHex(body(new SM_LEGION_EDIT(0x0B, legion))));
		legion.setJoinSettings(0, 0, "Teste");
		assertEquals("0b" + "54006500730074006500" + "0000" + "00" + "0000", HEX.formatHex(body(new SM_LEGION_EDIT(0x0B, legion))));
		legion.setActivity(2, 3, 0);
		assertEquals("0c0200000003000000", HEX.formatHex(body(new SM_LEGION_EDIT(0x0C, legion))));
		// favorito no C de cada receita do S 0x15A (logins de 16:40 e 16:49)
		byte[] craft = body(new SM_LEGION_CRAFT_LIST(List.of(new SM_LEGION_CRAFT_LIST.Recipe(1, 0, true, List.of()))));
		assertEquals("0100" + "01000000" + "00000000" + "00000000" + "0000" + "01" + "01", HEX.formatHex(craft));
		assertTrue(LegionPermissionsMask.CRAFT.can(0x7E0C) && !LegionPermissionsMask.CRAFT.can(0x5E0C));
		assertTrue(LegionPermissionsMask.BUFF.can(0x7E0C) && !LegionPermissionsMask.BUFF.can(0x3E0C));
	}

	@Test
	void applicantPacketsMatchNovaPasta() throws Exception {
		// Nova Pasta 2026-09-29 16:49: busca pela Lost Academy (S 0x150, 77 b), candidatura do Schelp (S 0x151, 30 b), lista do líder (S 0x152, 40 b),
		// aceite (S 0x154) e a entrada do Schelp offline (S 0x6E, 53 b)
		String lostAcademy = HEX.formatHex("Lost Academy\0".getBytes(StandardCharsets.UTF_16LE));
		String teste = HEX.formatHex("Teste\0".getBytes(StandardCharsets.UTF_16LE));
		String schelp = HEX.formatHex("Schelp\0".getBytes(StandardCharsets.UTF_16LE));
		assertEquals("0100" + "1738002e" + lostAcademy + HEX.formatHex("Kodra\0".getBytes(StandardCharsets.UTF_16LE)) + "01" + "02000000" + teste + "00"
			+ "0000" + "02000000" + "00000000" + "01000000" + "01", HEX.formatHex(body(new SM_LEGION_SEARCH_LIST(List.of(
				new SM_LEGION_SEARCH_LIST.Entry(0x2E003817, "Lost Academy", "Kodra", 1, 2, "Teste", 0, 0, 2, 0, 1)), true))));
		assertEquals("1738002e" + lostAcademy, HEX.formatHex(body(new SM_LEGION_APPLICATION(0x2E003817, "Lost Academy"))));
		assertEquals("000000000000", HEX.formatHex(body(new SM_LEGION_APPLICATION())));
		assertEquals("ffff" + "bb4c0f2e" + schelp + "0b01" + "3c00" + teste + "9916bc6a", HEX.formatHex(body(new SM_LEGION_APPLICANT_LIST(List.of(
			new LegionApplicant(0x2E0F4CBB, 0x2E003817, "Schelp", 11, 1, 60, "Teste", 0x6ABC1699, false))))));
		assertEquals("0000", HEX.formatHex(body(new SM_LEGION_APPLICANT_LIST(List.of()))));
		// 17:59: três candidatos, [H -3]
		assertEquals("fdff" + "1f2e0f2e" + HEX.formatHex("Sclepius\0".getBytes(StandardCharsets.UTF_16LE)) + "0a00" + "3c00"
			+ HEX.formatHex("safa\0".getBytes(StandardCharsets.UTF_16LE)) + "5627bc6a", HEX.formatHex(Arrays.copyOf(body(new SM_LEGION_APPLICANT_LIST(List.of(
				new LegionApplicant(0x2E0F2E1F, 0x2E003817, "Sclepius", 10, 0, 60, "safa", 0x6ABC2756, false),
				new LegionApplicant(0x2E0F34A1, 0x2E003817, "Kodrarik", 1, 0, 60, "s", 0x6ABC26EE, false),
				new LegionApplicant(0x2E0F4FB1, 0x2E003817, "Sertralina", 2, 1, 60, "re", 0x6ABC2716, false)))), 42)));
		assertEquals("bb4c0f2e01", HEX.formatHex(body(new SM_LEGION_APPLICANT_RESULT(0x2E0F4CBB, SM_LEGION_APPLICANT_RESULT.ACCEPTED))));
		// 18:08: candidata nova para o líder online (S 0x153) e busca pela apresentação sem resultado
		assertEquals("f127462e" + HEX.formatHex("Kimmie\0".getBytes(StandardCharsets.UTF_16LE)) + "0b01" + "0300"
			+ HEX.formatHex("oi\0".getBytes(StandardCharsets.UTF_16LE)) + "3f29bc6a", HEX.formatHex(body(new SM_LEGION_APPLICANT_ADD(
				new LegionApplicant(0x2E4627F1, 0x2E003817, "Kimmie", 11, 1, 3, "oi", 0x6ABC293F, false)))));
		assertEquals("000001", HEX.formatHex(body(new SM_LEGION_SEARCH_LIST(List.of(), true))));
		NetworkConfig.GAMESERVER_ID = 23;
		LegionMember member = member(new Legion(0x2E003817, "Lost Academy"), 0x2E0F4CBB, "Schelp", PlayerClass.CHANTER, 60, LegionRank.VOLUNTEER,
			120010000, false, 0x6ABC16FC);
		assertEquals("bb4c0f2e" + schelp + "04000b3c" + "10352707" + "00" + "fc16bc6a" + "17000000" + "24d71300" + schelp,
			HEX.formatHex(body(new SM_LEGION_ADD_MEMBER(member, 1300260, "Schelp"))));
	}

	@Test
	void itemCraftMatchesNovaPasta() throws Exception {
		// Nova Pasta 2026-09-29 16:02: 10000 kinah doados para a receita 300 e, depois do C_GUILD [15][D 300], a produção iniciada
		assertEquals("01002c01000000000000000000000100" + "0134df0a" + "10270000" + "0001", HEX.formatHex(body(new SM_LEGION_CRAFT_LIST(
			List.of(new SM_LEGION_CRAFT_LIST.Recipe(300, List.of(new SM_LEGION_CRAFT_LIST.Component(182400001, 10000))))))));
		assertEquals("01002c010000960bbc6a000000000100" + "0134df0a" + "00000000" + "0001", HEX.formatHex(body(new SM_LEGION_CRAFT_LIST(
			List.of(new SM_LEGION_CRAFT_LIST.Recipe(300, 0x6ABC0B96, List.of(new SM_LEGION_CRAFT_LIST.Component(182400001, 0))))))));
		// avisos de histórico: 08 geral, 0A armazém, 0D produção
		assertEquals("0a", HEX.formatHex(body(new SM_LEGION_EDIT(0x0A))));
		assertEquals("0d", HEX.formatHex(body(new SM_LEGION_EDIT(0x0D))));
		// aba 3 com o início de produção: ação 20, quem produziu e [item_text:produto]
		byte[] history = body(new SM_LEGION_HISTORY(List.of(new LegionHistoryEntry(1, 0x6ABC0B5A, LegionHistoryAction.CRAFT_START, "Kodra",
			"[item_text:188053047]")), LegionHistoryAction.Type.CRAFT));
		assertEquals("010000000000000001000000" + "5a0bbc6a" + "1400" + "4b006f00640072006100", HEX.formatHex(Arrays.copyOf(history, 28)));
		assertEquals("0300", HEX.formatHex(Arrays.copyOfRange(history, history.length - 2, history.length)));
	}

	@Test
	void donationPacketsMatchLostAcademy() throws Exception {
		// criação: primeira lista do dia (grupo 13 = candy_dark, Legion asmodiana)
		Map<Integer, Integer> selection = new LinkedHashMap<>();
		int[][] pairs = { { 7, 14 }, { 8, 8 }, { 9, 8 }, { 10, 1 }, { 11, 12 }, { 13, 1 }, { 14, 1 }, { 15, 3 } };
		for (int[] pair : pairs)
			selection.put(pair[0], pair[1]);
		assertEquals("0800070000000e000000080000000800000009000000080000000a000000010000000b0000000c0000000d000000010000000e000000010000000f00000003000000",
			HEX.formatHex(body(new SM_LEGION_DONATION_LIST(selection))));
		// primeira produção do Kodra: [13][D 10][D 1]
		assertEquals("0100d95b0f2e010000000100000001",
			HEX.formatHex(body(new SM_LEGION_DONATION_MEMBERS(List.of(new SM_LEGION_DONATION_MEMBERS.Entry(0x2E0F5BD9, 1, 1))))));
		assertEquals("8d0c0200", HEX.formatHex(body(new SM_LEGION_COIN(0x20C8D))));
		assertEquals("0100000001000000", HEX.formatHex(body(new SM_LEGION_DONATION_STATUS(1, 1))));
		assertEquals("01000000", HEX.formatHex(body(new SM_LEGION_DONATION_POINTS(1))));
		assertEquals("19000000000043641500015b006900740065006d003a003100360032003000300030003000360039005d00000000",
			HEX.formatHex(body(new SM_SYSTEM_MESSAGE(1401923, "[item:162000069]")))); // 46 b, captura
		assertEquals("190000000000416415000000", HEX.formatHex(body(new SM_SYSTEM_MESSAGE(1401921))));
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
