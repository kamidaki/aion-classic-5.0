package com.aionemu.gameserver.services;

import java.sql.SQLException;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.LegionConfig;
import com.aionemu.gameserver.dao.LegionDonationDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.LegionDonationData;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionDonationBoard;
import com.aionemu.gameserver.model.team.legion.LegionDonationProgress;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_COIN;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_DONATION_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_DONATION_MEMBERS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_DONATION_POINTS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_DONATION_STATUS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Produção de moedas pessoais da Legion (aba 주화 생산, C_GUILD 0x13), reconstruída da criação da Lost Academy (outros2 2026-09-22 10:23: dez
 * produções [13][D 10][D 1] do Kodra) e das listas do dia de 06/09 a 28/09.
 * <p>
 * Resposta oficial de cada produção, nesta ordem: item consumido, S 0x156 (quem produziu), S 0x165 (moedas), S 0x158 (produções hoje e dias
 * seguidos), STR_MSG_GUILD_DONATION_ITEM, S 0x157 (pontos da Legion) e STR_MSG_GUILD_DONATION_GET_GUILD_POINT.
 * <p>
 * PENDENTE_DE_COMPROVACAO: o limite diário (gameserver.legion.donation.dailylimit; nas capturas só se chegou a 10 sem erro), o sorteio da
 * lista (ver {@link LegionDonationBoard}), quem além do produtor recebe o S 0x156 e o S 0x157 (a captura tem um membro só) e a entrega das
 * recompensas por dias seguidos e por pontos da Legion (client_guild_donation_reward), que nenhuma captura mostra.
 */
public class LegionDonationService {

	private static final Logger log = LoggerFactory.getLogger(LegionDonationService.class);

	private final Map<Integer, LegionDonationBoard> boards = new ConcurrentHashMap<>();
	private final Map<Integer, LegionDonationProgress> progressByPlayer = new ConcurrentHashMap<>();
	private final Set<Integer> loadedLegions = ConcurrentHashMap.newKeySet();

	public static LegionDonationService getInstance() {
		return SingletonHolder.instance;
	}

	private LegionDonationService() {
	}

	/**
	 * @return o dia de produção: vira no reset_time do client_guild_donation_setting.xml (08:00), no fuso do servidor
	 */
	public static LocalDate today(LocalDateTime now, LocalTime resetTime) {
		return now.minusHours(resetTime.getHour()).minusMinutes(resetTime.getMinute()).toLocalDate();
	}

	private static LocalDate today() {
		return today(LocalDateTime.now(), DataManager.LEGION_DONATION_DATA.getResetTime());
	}

	/**
	 * Login ou entrada na Legion: lista do dia, produção do personagem, moedas e os pontos de cada membro. No login oficial os três primeiros vêm
	 * antes do S_GUILD_INFO e o S 0x156 depois da lista de membros; aqui vêm juntos depois dela.
	 */
	public void sendState(Player player) {
		Legion legion = player.getLegion();
		if (legion == null)
			return;
		LocalDate today = today();
		LegionDonationBoard board = getBoard(legion, player.getRace(), today);
		LegionDonationProgress progress = getProgress(player.getObjectId());
		if (board == null || progress == null)
			return;
		PacketSendUtility.sendPacket(player, new SM_LEGION_DONATION_LIST(board.getSelection()));
		PacketSendUtility.sendPacket(player, new SM_LEGION_DONATION_STATUS(progress.getCountToday(today), progress.getStreak(today)));
		PacketSendUtility.sendPacket(player, new SM_LEGION_COIN(progress.getCoins()));
		PacketSendUtility.sendPacket(player, new SM_LEGION_DONATION_POINTS(board.getPoints()));
		PacketSendUtility.sendPacket(player, new SM_LEGION_DONATION_MEMBERS(entries(legion, today)));
	}

	/**
	 * C_GUILD 0x13 [D grupo][D índice].
	 */
	public void produce(Player player, int groupId, int index) {
		Legion legion = player.getLegion();
		if (legion == null)
			return;
		LocalDate today = today();
		LegionDonationBoard board = getBoard(legion, player.getRace(), today);
		LegionDonationProgress progress = getProgress(player.getObjectId());
		LegionDonationData.Group group = DataManager.LEGION_DONATION_DATA.getGroup(groupId);
		LegionDonationData.Entry entry = group == null ? null : group.getEntry(index);
		if (board == null || progress == null || entry == null || !Integer.valueOf(index).equals(board.getSelection().get(groupId))) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401957)); // STR_MSG_GUILD_DONATION_FAIL
			return;
		}
		synchronized (progress) {
			if (progress.getCountToday(today) >= LegionConfig.LEGION_DONATION_DAILY_LIMIT) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401926)); // STR_MSG_GUILD_DONATION_MAX_COUNT
				return;
			}
			if (player.getInventory().getItemCountByItemId(entry.getItemId()) < entry.getCount()
				|| !player.getInventory().decreaseByItemId(entry.getItemId(), entry.getCount())) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401927)); // STR_MSG_GUILD_DONATION_NOT_ENOUGH_ITEM
				return;
			}
			progress.produce(today, entry.getPoints(), entry.getCoins());
			LegionDonationDAO.storeProgress(player.getObjectId(), progress);
		}
		int legionPoints = board.addPoints(entry.getPoints());
		LegionDonationDAO.storeBoard(legion.getLegionId(), board);

		SM_LEGION_DONATION_MEMBERS memberUpdate = new SM_LEGION_DONATION_MEMBERS(
			List.of(new SM_LEGION_DONATION_MEMBERS.Entry(player.getObjectId(), progress.getPointsToday(today), progress.getPointsTotal())));
		PacketSendUtility.broadcastToLegion(legion, memberUpdate);
		PacketSendUtility.sendPacket(player, new SM_LEGION_COIN(progress.getCoins()));
		PacketSendUtility.sendPacket(player, new SM_LEGION_DONATION_STATUS(progress.getCountToday(today), progress.getStreak(today)));
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401923, "[item:" + entry.getItemId() + "]")); // STR_MSG_GUILD_DONATION_ITEM
		PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_DONATION_POINTS(legionPoints));
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401921)); // STR_MSG_GUILD_DONATION_GET_GUILD_POINT
	}

	/**
	 * Pontos da doação para a produção (C_GUILD 0x14): sobem no S 0x156 (Kodra 10 -> 11, 22/09), sem mexer nas produções do dia (S 0x158) nem nos
	 * pontos da Legion (S 0x157), que a captura não reenviou.
	 */
	public void addCraftPoints(Player player, int points) {
		LegionDonationProgress progress = getProgress(player.getObjectId());
		if (progress == null || player.getLegion() == null)
			return;
		LocalDate today = today();
		synchronized (progress) {
			progress.rollTo(today);
			progress.addPoints(points);
			LegionDonationDAO.storeProgress(player.getObjectId(), progress);
		}
		PacketSendUtility.broadcastToLegion(player.getLegion(), new SM_LEGION_DONATION_MEMBERS(
			List.of(new SM_LEGION_DONATION_MEMBERS.Entry(player.getObjectId(), progress.getPointsToday(today), progress.getPointsTotal()))));
	}

	/**
	 * @return pontos de produção de hoje e total do membro, para o fim do S_GUILD_MEMBER_INFO
	 */
	public int[] getMemberPoints(LegionMember member) {
		ensureLegionLoaded(member.getLegion());
		LegionDonationProgress progress = progressByPlayer.get(member.getObjectId());
		return progress == null ? new int[2] : new int[] { progress.getPointsToday(today()), progress.getPointsTotal() };
	}

	private List<SM_LEGION_DONATION_MEMBERS.Entry> entries(Legion legion, LocalDate today) {
		ensureLegionLoaded(legion);
		List<SM_LEGION_DONATION_MEMBERS.Entry> entries = new ArrayList<>();
		for (int memberId : legion.getMemberIds()) {
			LegionDonationProgress progress = progressByPlayer.get(memberId);
			entries.add(new SM_LEGION_DONATION_MEMBERS.Entry(memberId, progress == null ? 0 : progress.getPointsToday(today),
				progress == null ? 0 : progress.getPointsTotal()));
		}
		return entries;
	}

	private LegionDonationBoard getBoard(Legion legion, Race race, LocalDate today) {
		LegionDonationBoard board = boards.computeIfAbsent(legion.getLegionId(), id -> {
			try {
				LegionDonationBoard stored = LegionDonationDAO.loadBoard(id);
				return stored == null ? new LegionDonationBoard(null, Map.of(), 0) : stored;
			} catch (SQLException e) {
				log.error("Could not load legion donation board of " + legion, e);
				return null;
			}
		});
		if (board != null && board.rollTo(today, DataManager.LEGION_DONATION_DATA.getGroups(race), ThreadLocalRandom.current()))
			LegionDonationDAO.storeBoard(legion.getLegionId(), board);
		return board;
	}

	/**
	 * @return o progresso do personagem, ou null se o banco falhou (seguir com um vazio apagaria as moedas na próxima gravação)
	 */
	private LegionDonationProgress getProgress(int playerId) {
		return progressByPlayer.computeIfAbsent(playerId, id -> {
			try {
				return LegionDonationDAO.loadProgress(id);
			} catch (SQLException e) {
				log.error("Could not load legion donation progress of player " + id, e);
				return null;
			}
		});
	}

	private void ensureLegionLoaded(Legion legion) {
		if (!loadedLegions.add(legion.getLegionId()))
			return;
		try {
			LegionDonationDAO.loadLegionProgress(legion.getLegionId()).forEach(progressByPlayer::putIfAbsent);
		} catch (SQLException e) {
			loadedLegions.remove(legion.getLegionId());
			log.error("Could not load legion donation progress of " + legion, e);
		}
	}

	private static class SingletonHolder {

		protected static final LegionDonationService instance = new LegionDonationService();
	}
}
