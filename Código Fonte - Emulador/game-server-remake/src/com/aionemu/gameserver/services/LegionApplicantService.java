package com.aionemu.gameserver.services;

import java.util.ArrayList;
import java.util.List;

import com.aionemu.gameserver.dao.LegionApplicantDAO;
import com.aionemu.gameserver.dao.LegionMemberDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.LegionSettingsData;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionApplicant;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.model.team.legion.LegionPermissionsMask;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_APPLICANT_ADD;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_APPLICANT_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_APPLICANT_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_APPLICATION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_SEARCH_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;

/**
 * Busca de Legion e candidaturas, conferidas na Nova Pasta 2026-09-29 16:49 (Kodra líder da Lost Academy e Schelp sem Legion no mesmo cliente):
 * <ul>
 * <li>busca (C 0x118) → S 0x150; candidatura (C 0x119) → S 0x151 com a Legion; cancelamento (C 0x11A) → S 0x151 vazio;</li>
 * <li>login do candidato: S 0x151 com a candidatura, ou STR_GUILD_JOIN_REFUSAL e S 0x151 vazio depois de recusado;</li>
 * <li>login do membro: S 0x152 com os candidatos;</li>
 * <li>C_GUILD 0x12 [D candidato] recusa (S 0x154 2); 0x11 aceita (S 0x154 1, S 0x6E do candidato offline com STR_GUILD_INVITE_HE_JOINED e
 * histórico de entrada).</li>
 * </ul>
 * Na Nova Pasta 2026-09-29 17:59: entrada direta na Connection Lost (forma 1), três candidatos no S 0x152 e três aceites offline seguidos.
 * <p>
 * Na Nova Pasta 2026-09-29 18:08 (dois clientes): o líder online recebe o candidato novo no S 0x153 e a candidata online aceita recebe a
 * entrada normal, o S 0x151 vazio e STR_GUILD_JOIN_APPORVE.
 * <p>
 * Na 18:22, a recusa com o candidato online: S 0x151 vazio e STR_GUILD_JOIN_REFUSAL. A lista geral é o ranking de Legions da raça (as 50 da
 * busca na ordem do Abyss Ranking de Legions, print de 18:22), 34 por pacote como nas capturas.
 * <p>
 * Só quem tem a permissão Invite/Approve vê e responde os candidatos. A busca por texto segue a contribuição (ordem oficial desconhecida).
 * PENDENTE_DE_COMPROVACAO: o pacote que tira o candidato da aba do líder online quando ele cancela (aqui o S 0x152 de novo).
 */
public class LegionApplicantService {

	private static final int SEARCH_LIMIT = 50;
	private static final int SEARCH_PAGE = 34;

	public static LegionApplicantService getInstance() {
		return SingletonHolder.instance;
	}

	private LegionApplicantService() {
	}

	/**
	 * @param text
	 *          trecho do nome ou da apresentação ({@code intro}), ou null para a lista geral
	 */
	public void search(Player player, String text, boolean intro) {
		List<SM_LEGION_SEARCH_LIST.Entry> entries = new ArrayList<>();
		String filter = text == null || text.isBlank() ? null : text.trim();
		for (int legionId : LegionApplicantDAO.search(player.getRace(), filter, intro && filter != null, SEARCH_LIMIT)) {
			Legion legion = LegionService.getInstance().getLegion(legionId);
			LegionMember leader = leaderOf(legion);
			if (leader != null)
				entries.add(new SM_LEGION_SEARCH_LIST.Entry(legion.getLegionId(), legion.getName(), leader.getName(), legion.getLegionLevel(),
					legion.getMemberIds().size(), legion.getJoinIntro(), legion.getJoinType(), legion.getJoinMinLevel(), legion.getCampaignActivity(),
					legion.getLegionActivity(), legion.getGrowthLevel()));
		}
		for (int from = 0; from < entries.size() || from == 0; from += SEARCH_PAGE) {
			int to = Math.min(entries.size(), from + SEARCH_PAGE);
			PacketSendUtility.sendPacket(player, new SM_LEGION_SEARCH_LIST(entries.subList(from, to), to == entries.size()));
		}
	}

	public void apply(Player player, int legionId, String intro) {
		if (player.isLegionMember() || intro == null || intro.length() > 32)
			return;
		Legion legion = LegionService.getInstance().getLegion(legionId);
		if (leaderOf(legion) == null) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1300329)); // STR_GUILD_INVITE_CAN_NOT_JOIN_NOT_EXISTS
			return;
		}
		if (legion.getJoinType() == 2) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401878)); // STR_MSG_GUILD_CANT_JOIN
			return;
		}
		if (player.getLevel() < legion.getJoinMinLevel()) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401879)); // STR_MSG_GUILD_CANT_JOIN_MAX_LEVEL
			return;
		}
		if (isFull(legion)) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401881)); // STR_MSG_GUILD_CANT_JOIN_MAX_MEMBER
			return;
		}
		if (legion.getJoinType() == 1) { // Everyone can join: entra direto, sem S 0x151 (Connection Lost, Nova Pasta 2026-09-29 17:59)
			LegionApplicantDAO.delete(player.getObjectId());
			LegionService.getInstance().addToLegion(legion, player, player);
			return;
		}
		LegionApplicant applicant = new LegionApplicant(player.getObjectId(), legionId, player.getName(),
			player.getCommonData().getPlayerClass().getClassId(), player.getGender().getGenderId(), player.getLevel(), intro,
			(int) (System.currentTimeMillis() / 1000), false);
		if (LegionApplicantDAO.store(applicant)) {
			PacketSendUtility.sendPacket(player, new SM_LEGION_APPLICATION(legionId, legion.getName()));
			for (Player member : legion.getOnlinePlayers()) // S 0x153 para o líder online (Nova Pasta 2026-09-29 18:08)
				if (member.getLegionMember() != null && member.getLegionMember().hasRights(LegionPermissionsMask.INVITE))
					PacketSendUtility.sendPacket(member, new SM_LEGION_APPLICANT_ADD(applicant));
		}
	}

	public void cancel(Player player, int legionId) {
		LegionApplicant applicant = LegionApplicantDAO.loadByPlayer(player.getObjectId());
		if (applicant == null || applicant.legionId() != legionId)
			return;
		LegionApplicantDAO.delete(player.getObjectId());
		PacketSendUtility.sendPacket(player, new SM_LEGION_APPLICATION());
		// o candidato some da aba do líder, sem mensagem (confirmado em jogo); sem captura do lado do líder, a lista vai de novo no S 0x152
		Legion legion = LegionService.getInstance().getLegion(legionId);
		if (legion != null)
			for (Player member : legion.getOnlinePlayers())
				if (member.getLegionMember() != null && member.getLegionMember().hasRights(LegionPermissionsMask.INVITE))
					sendApplicants(member);
	}

	/**
	 * C_GUILD 0x11 [D candidato]
	 */
	public void accept(Player approver, int playerId) {
		LegionApplicant applicant = getApplicant(approver, playerId);
		if (applicant == null)
			return;
		Legion legion = approver.getLegion();
		Player target = World.getInstance().getPlayer(playerId);
		if (target != null ? target.isLegionMember() : LegionMemberDAO.isIdUsed(playerId)) {
			LegionApplicantDAO.delete(playerId);
			PacketSendUtility.sendPacket(approver, new SM_SYSTEM_MESSAGE(1300288)); // STR_GUILD_INVITE_CAN_NOT_JOIN_TO_GUILD
			return;
		}
		if (isFull(legion)) {
			PacketSendUtility.sendPacket(approver, SM_SYSTEM_MESSAGE.STR_GUILD_INVITE_CAN_NOT_ADD_MEMBER_ANY_MORE());
			return;
		}
		LegionApplicantDAO.delete(playerId);
		PacketSendUtility.sendPacket(approver, new SM_LEGION_APPLICANT_RESULT(playerId, SM_LEGION_APPLICANT_RESULT.ACCEPTED));
		if (target != null) {
			// Kimmie online (Nova Pasta 2026-09-29 18:08): a entrada normal, o S 0x151 vazio e STR_GUILD_JOIN_APPORVE
			if (LegionService.getInstance().addToLegion(legion, target, approver)) {
				PacketSendUtility.sendPacket(target, new SM_LEGION_APPLICATION());
				PacketSendUtility.sendPacket(target, new SM_SYSTEM_MESSAGE(1401890)); // STR_GUILD_JOIN_APPORVE
			}
		} else {
			LegionService.getInstance().addOfflineMember(legion, playerId);
		}
	}

	/**
	 * C_GUILD 0x12 [D candidato]
	 */
	public void refuse(Player approver, int playerId) {
		LegionApplicant applicant = getApplicant(approver, playerId);
		if (applicant == null)
			return;
		PacketSendUtility.sendPacket(approver, new SM_LEGION_APPLICANT_RESULT(playerId, SM_LEGION_APPLICANT_RESULT.REFUSED));
		Player target = World.getInstance().getPlayer(playerId);
		if (target == null) {
			LegionApplicantDAO.refuse(playerId, applicant.legionId());
		} else {
			// Kimmie online (Nova Pasta 2026-09-29 18:22): o S 0x151 vazio e depois STR_GUILD_JOIN_REFUSAL
			LegionApplicantDAO.delete(playerId);
			PacketSendUtility.sendPacket(target, new SM_LEGION_APPLICATION());
			PacketSendUtility.sendPacket(target, new SM_SYSTEM_MESSAGE(1401889)); // STR_GUILD_JOIN_REFUSAL
		}
	}

	private LegionApplicant getApplicant(Player approver, int playerId) {
		LegionMember member = approver.getLegionMember();
		if (member == null)
			return null;
		if (!member.hasRights(LegionPermissionsMask.INVITE)) {
			PacketSendUtility.sendPacket(approver, SM_SYSTEM_MESSAGE.STR_GUILD_INVITE_DONT_HAVE_RIGHT_TO_INVITE());
			return null;
		}
		LegionApplicant applicant = LegionApplicantDAO.loadByPlayer(playerId);
		return applicant == null || applicant.refused() || applicant.legionId() != member.getLegion().getLegionId() ? null : applicant;
	}

	/**
	 * S 0x151 do login: a candidatura em aberto, ou vazio (com STR_GUILD_JOIN_REFUSAL antes se ela foi recusada enquanto estava offline).
	 */
	public void onEnterWorld(Player player) {
		LegionApplicant applicant = LegionApplicantDAO.loadByPlayer(player.getObjectId());
		Legion legion = applicant == null || player.isLegionMember() ? null : LegionService.getInstance().getLegion(applicant.legionId());
		if (applicant != null && (legion == null || applicant.refused())) {
			LegionApplicantDAO.delete(player.getObjectId());
			if (applicant.refused())
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401889)); // STR_GUILD_JOIN_REFUSAL
			legion = null;
		}
		PacketSendUtility.sendPacket(player, legion == null ? new SM_LEGION_APPLICATION() : new SM_LEGION_APPLICATION(legion.getLegionId(), legion.getName()));
	}

	/**
	 * S 0x152 do login do membro: os candidatos para quem pode aceitar, lista vazia para os demais.
	 */
	public void sendApplicants(Player player) {
		LegionMember member = player.getLegionMember();
		List<LegionApplicant> applicants = member != null && member.hasRights(LegionPermissionsMask.INVITE)
			? LegionApplicantDAO.loadByLegion(member.getLegion().getLegionId()) : List.of();
		PacketSendUtility.sendPacket(player, new SM_LEGION_APPLICANT_LIST(applicants));
	}

	private static LegionMember leaderOf(Legion legion) {
		return legion == null ? null : legion.streamMembers().filter(LegionMember::isBrigadeGeneral).findFirst().orElse(null);
	}

	private static boolean isFull(Legion legion) {
		LegionSettingsData.Level level = DataManager.LEGION_SETTINGS_DATA.getLevel(legion.getLegionLevel());
		return level == null || legion.getMemberIds().size() >= level.getMaxMembers();
	}

	private static class SingletonHolder {

		protected static final LegionApplicantService instance = new LegionApplicantService();
	}
}
