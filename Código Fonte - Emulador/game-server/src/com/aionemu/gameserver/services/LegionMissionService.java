package com.aionemu.gameserver.services;

import java.sql.SQLException;
import java.time.DayOfWeek;
import java.time.Instant;
import java.time.LocalTime;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.LegionMissionDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.LegionMissionData;
import com.aionemu.gameserver.dataholders.LegionMissionData.ActionType;
import com.aionemu.gameserver.dataholders.LegionMissionData.Activity;
import com.aionemu.gameserver.dataholders.LegionMissionData.Mission;
import com.aionemu.gameserver.dataholders.LegionMissionData.Period;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionMissionProgress;
import com.aionemu.gameserver.model.team.legion.LegionMissionProgress.Owner;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_ESSENCE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_GROWTH;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_MISSION_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_MISSION_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Missões da Legion ("Campaigns"), reconstruídas das capturas oficiais: lista S 0x15C (25 pacotes), progresso S 0x15D (153) e a recompensa
 * automática do estágio (outros2 2026-09-22 19:22: STR_MSG_GUILD_MISSION_SUCCESS, STR_GUILD_GROWTH_GET_EXP 3000, S 0x163, S 0x164 e
 * STR_GUILD_GET_ESSENCE_PIECE 10 quando a diária chegou a 3 ações concluídas).
 * <p>
 * Períodos (horários do S 0x15C): a diária começa às 07:00 UTC e a semanal e a de retorno na quarta-feira às 07:00 UTC. A diária e a de retorno
 * são do personagem e a semanal é da Legion inteira (escolha do usuário em 29/09). Só as missões de atividade NONE entram: é a única que as
 * Legions capturadas usam.
 * <p>
 * PENDENTE_DE_COMPROVACAO: quem define a atividade da Legion, o critério da missão de retorno, o limite diário de recompensas
 * (STR_MSG_GUILD_MISSION_DAILY_REWARD_MAX) e a condição de mundo do PvP (devapass_exclusion_world_01, sem definição no cliente).
 */
public class LegionMissionService {

	private static final Logger log = LoggerFactory.getLogger(LegionMissionService.class);
	public static final LocalTime RESET_TIME = LocalTime.of(7, 0);
	private static final List<Period> PERIODS = List.of(Period.DAILY, Period.WEEKLY, Period.RETURN);

	private final Map<String, LegionMissionProgress> cache = new ConcurrentHashMap<>();
	private final AtomicLong nextInstanceId = new AtomicLong(-1);

	public static LegionMissionService getInstance() {
		return SingletonHolder.instance;
	}

	private LegionMissionService() {
	}

	/**
	 * @return início do período que contém {@code now}, em segundos
	 */
	public static long periodStart(Period period, Instant now) {
		ZonedDateTime utc = now.atZone(ZoneOffset.UTC);
		ZonedDateTime start = utc.toLocalDate().atTime(RESET_TIME).atZone(ZoneOffset.UTC);
		if (period != Period.DAILY)
			start = start.with(TemporalAdjusters.previousOrSame(DayOfWeek.WEDNESDAY));
		if (utc.isBefore(start))
			start = period == Period.DAILY ? start.minusDays(1) : start.minusWeeks(1);
		return start.toEpochSecond();
	}

	public static int periodCode(Period period) {
		return switch (period) {
			case DAILY -> 1;
			case WEEKLY -> 2;
			case RETURN -> 7;
		};
	}

	private static Owner owner(Period period) {
		return period == Period.WEEKLY ? Owner.LEGION : Owner.PLAYER;
	}

	/**
	 * Login, criação e entrada na Legion.
	 */
	public void sendState(Player player) {
		Legion legion = player.getLegion();
		if (legion == null)
			return;
		Instant now = Instant.now();
		List<SM_LEGION_MISSION_LIST.Mission> missions = new ArrayList<>();
		for (Mission mission : missions(player)) {
			LegionMissionProgress progress = getProgress(player, legion, mission, now);
			if (progress != null)
				missions.add(toPacket(mission, progress));
		}
		missions.sort(Comparator.comparingInt(SM_LEGION_MISSION_LIST.Mission::missionId));
		PacketSendUtility.sendPacket(player, new SM_LEGION_MISSION_LIST((int) now.getEpochSecond(), missions));
	}

	/**
	 * Um evento de jogo que pode contar numa ação.
	 *
	 * @param targetId
	 *          item, NPC, quest ou mundo, conforme o tipo
	 * @param targetLevel
	 *          nível do NPC, para o level_gap da caça (0 nos outros tipos)
	 */
	public void onEvent(Player player, ActionType type, int targetId, int amount, int targetLevel) {
		Legion legion = player.getLegion();
		if (legion == null || amount <= 0)
			return;
		Instant now = Instant.now();
		for (Mission mission : missions(player)) {
			for (int actionId : mission.getActionIds()) {
				LegionMissionData.Action action = DataManager.LEGION_MISSION_DATA.getAction(actionId);
				if (action.getType() != type || !action.matches(targetId))
					continue;
				if (action.getLevelGap() > 0 && targetLevel > 0 && targetLevel < player.getLevel() - action.getLevelGap())
					continue;
				LegionMissionProgress progress = getProgress(player, legion, mission, now);
				if (progress != null)
					progress(player, legion, mission, progress, action, amount, now);
			}
		}
	}

	private void progress(Player player, Legion legion, Mission mission, LegionMissionProgress progress, LegionMissionData.Action action, int amount,
		Instant now) {
		int value = progress.addProgress(action.getId(), amount, action.getMaxProgress(), now.getEpochSecond());
		if (value < 0)
			return;
		Owner owner = owner(mission.getPeriod());
		List<Player> receivers = owner == Owner.LEGION ? legion.getOnlinePlayers() : List.of(player);
		long actionInstance = progress.getAction(action.getId()).getInstanceId();
		if (value < action.getMaxProgress()) {
			store(owner, player, legion, progress);
			receivers.forEach(p -> PacketSendUtility.sendPacket(p, new SM_LEGION_MISSION_UPDATE(List.of(new SM_LEGION_MISSION_UPDATE.Entry(actionInstance, 1, value)))));
			return;
		}
		int completed = completedActions(progress);
		receivers.forEach(p -> PacketSendUtility.sendPacket(p, new SM_SYSTEM_MESSAGE(1401906))); // STR_MSG_GUILD_MISSION_SUCCESS
		rewardStages(legion, mission, progress, completed, receivers);
		store(owner, player, legion, progress);
		SM_LEGION_MISSION_UPDATE update = new SM_LEGION_MISSION_UPDATE(
			List.of(new SM_LEGION_MISSION_UPDATE.Entry(actionInstance, 2, value), new SM_LEGION_MISSION_UPDATE.Entry(progress.getInstanceId(), 1, completed)));
		receivers.forEach(p -> PacketSendUtility.sendPacket(p, update));
	}

	/**
	 * Estágios acumulam: o estágio k sai quando as ações concluídas chegam à soma dos count até ele (diária 4: 3 ações, depois mais 2).
	 */
	private void rewardStages(Legion legion, Mission mission, LegionMissionProgress progress, int completed, List<Player> receivers) {
		synchronized (progress) {
			List<LegionMissionData.Stage> stages = mission.getStages();
			int needed = 0;
			for (int i = 0; i < stages.size(); i++) {
				needed += stages.get(i).getCount();
				if (i < progress.getRewardedStages())
					continue;
				if (completed < needed)
					break;
				progress.setRewardedStages(i + 1);
				giveReward(legion, stages.get(i), receivers);
			}
		}
	}

	private void giveReward(Legion legion, LegionMissionData.Stage stage, List<Player> receivers) {
		int levels = 0;
		if (stage.getExp() > 0) {
			levels = legion.addGrowthExp(stage.getExp());
			receivers.forEach(p -> PacketSendUtility.sendPacket(p, new SM_SYSTEM_MESSAGE(1401914, String.valueOf(stage.getExp())))); // STR_GUILD_GROWTH_GET_EXP
		}
		legion.addEssence(stage.getEssence(), stage.getEssencePiece());
		LegionMissionDAO.storeGrowth(legion);
		PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_ESSENCE(legion.getEssence(), legion.getEssencePiece()));
		PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_GROWTH(legion.getGrowthLevel(), legion.getGrowthExp()));
		if (levels > 0) // STR_GUILD_GROWTH_LEVEL_UP
			PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401915, String.valueOf(legion.getGrowthLevel())));
		if (stage.getEssence() > 0) // STR_GUILD_GET_ESSENCE
			receivers.forEach(p -> PacketSendUtility.sendPacket(p, new SM_SYSTEM_MESSAGE(1401979, String.valueOf(stage.getEssence()))));
		if (stage.getEssencePiece() > 0) // STR_GUILD_GET_ESSENCE_PIECE
			receivers.forEach(p -> PacketSendUtility.sendPacket(p, new SM_SYSTEM_MESSAGE(1401980, String.valueOf(stage.getEssencePiece()))));
	}

	private static int completedActions(LegionMissionProgress progress) {
		int completed = 0;
		for (LegionMissionProgress.Action action : progress.getActions()) {
			LegionMissionData.Action template = DataManager.LEGION_MISSION_DATA.getAction(action.getActionId());
			if (template != null && action.getProgress() >= template.getMaxProgress())
				completed++;
		}
		return completed;
	}

	private static List<Mission> missions(Player player) {
		List<Mission> missions = new ArrayList<>();
		for (Period period : PERIODS)
			for (Mission mission : DataManager.LEGION_MISSION_DATA.getMissions(period, player.getRace(), Activity.NONE))
				if (mission.isLevelAllowed(player.getLevel()))
					missions.add(mission);
		return missions;
	}

	private static SM_LEGION_MISSION_LIST.Mission toPacket(Mission mission, LegionMissionProgress progress) {
		List<SM_LEGION_MISSION_LIST.Action> actions = new ArrayList<>();
		for (LegionMissionProgress.Action action : progress.getActions()) {
			LegionMissionData.Action template = DataManager.LEGION_MISSION_DATA.getAction(action.getActionId());
			actions.add(new SM_LEGION_MISSION_LIST.Action(action.getInstanceId(), action.getActionId(), template.getCode(),
				action.getProgress() >= template.getMaxProgress(), action.getProgress(), action.getLastUpdate()));
		}
		return new SM_LEGION_MISSION_LIST.Mission(progress.getInstanceId(), mission.getId(), periodCode(mission.getPeriod()), progress.getPeriodStart(),
			progress.getLastUpdate(), actions);
	}

	/**
	 * @return a missão do dono no período atual (nova, com instâncias novas, se o período virou), ou null se o banco falhou
	 */
	private LegionMissionProgress getProgress(Player player, Legion legion, Mission mission, Instant now) {
		Owner owner = owner(mission.getPeriod());
		int ownerId = owner == Owner.LEGION ? legion.getLegionId() : player.getObjectId();
		long periodStart = periodStart(mission.getPeriod(), now);
		String key = owner.ordinal() + ":" + ownerId + ":" + mission.getId();
		try {
			return cache.compute(key, (k, current) -> {
				try {
					if (current == null)
						current = LegionMissionDAO.load(owner, ownerId, mission.getId());
				} catch (SQLException e) {
					throw new IllegalStateException(e);
				}
				if (current != null && current.getPeriodStart() == periodStart)
					return current;
				LegionMissionProgress created = create(mission, periodStart);
				LegionMissionDAO.store(owner, ownerId, created);
				return created;
			});
		} catch (IllegalStateException e) {
			log.error("Could not load legion mission " + mission.getId() + " of " + owner + " " + ownerId, e);
			return null;
		}
	}

	private LegionMissionProgress create(Mission mission, long periodStart) {
		List<Integer> actionIds = mission.getActionIds();
		long first = allocateInstances(actionIds.size() + 1);
		List<LegionMissionProgress.Action> actions = new ArrayList<>();
		for (int i = 0; i < actionIds.size(); i++)
			actions.add(new LegionMissionProgress.Action(actionIds.get(i), first + 1 + i, 0, periodStart));
		return new LegionMissionProgress(mission.getId(), first, periodStart, periodStart, 0, actions);
	}

	/**
	 * Instâncias em sequência (a da missão e as das ações), como no oficial; continuam da maior já gravada.
	 */
	private long allocateInstances(int count) {
		if (nextInstanceId.get() < 0) {
			synchronized (nextInstanceId) {
				if (nextInstanceId.get() < 0) {
					try {
						nextInstanceId.set(LegionMissionDAO.loadMaxInstanceId() + 1);
					} catch (SQLException e) {
						throw new IllegalStateException("Could not load legion mission instance ids", e);
					}
				}
			}
		}
		return nextInstanceId.getAndAdd(count);
	}

	private static void store(Owner owner, Player player, Legion legion, LegionMissionProgress progress) {
		LegionMissionDAO.store(owner, owner == Owner.LEGION ? legion.getLegionId() : player.getObjectId(), progress);
	}

	private static class SingletonHolder {

		protected static final LegionMissionService instance = new LegionMissionService();
	}
}
