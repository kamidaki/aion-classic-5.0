package com.lostacademy.lostsocket.secure;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.ZonedDateTime;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Future;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.dao.ParticipationPointsDAO;
import com.aionemu.gameserver.model.gameobjects.player.CustomPlayerState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.RequestResponseHandler;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ALTER_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_PLAYER_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_QUESTION_WINDOW;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.utils.time.ServerTime;

/**
 * Serviço completo de gerenciamento do Altar / Modo Eltar FFA (Secure Area / Battle Zone).
 * Controla ativação, confirmação com popup de custo, contagem de baixas, pontuação do Livro de Eltar,
 * recompensas e sincronização de pacotes de rede (CM_SERVER_PVP_ACK <> SM_ALTER_INFO).
 *
 * @author Lost Academy Team & Durak
 */
public class SecureAreaService {

	private static final Logger log = LoggerFactory.getLogger(SecureAreaService.class);

	public static final long FFA_COST_POINTS                    = 100L;
	public static final long FFA_CHARGE_MS                      = 10_000L;
	public static final long FFA_COOLDOWN_MS                    = 3_600_000L; // 1 hora
	public static final int  FFA_MIN_LEVEL                      = 50;
	public static final int  FFA_POINTS_PER_KILL                = 100;
	public static final long FFA_PARTICIPATION_REWARD_PER_KILL = 25L;
	public static final int  QUESTION_WINDOW_USE_COST_ID        = 160016; // STR_ASK_USE_ARTIFACT ("Using requires %1 %0. Proceed?")

	private static final ConcurrentHashMap<Integer, Long>             cooldownMap    = new ConcurrentHashMap<>();
	private static final ConcurrentHashMap<Integer, Future<?>>        pendingCharges = new ConcurrentHashMap<>();
	private static final ConcurrentHashMap<Integer, AlterPlayerStats> statsCache     = new ConcurrentHashMap<>();

	private static final SecureAreaService instance = new SecureAreaService();
	public static SecureAreaService getInstance() { return instance; }

	private SecureAreaService() {
		initTables();
	}

	/**
	 * Estrutura de dados de estatísticas e baixas do Altar.
	 */
	public static class AlterPlayerStats {
		public final int playerId;
		public volatile int alterKills;
		public volatile int alterPoints;
		public volatile int dailyKills;
		public volatile int weeklyKills;
		public volatile long lastKillTime;
		public volatile long lastResetTime;

		public AlterPlayerStats(int playerId, int alterKills, int alterPoints, int dailyKills, int weeklyKills, long lastKillTime, long lastResetTime) {
			this.playerId = playerId;
			this.alterKills = alterKills;
			this.alterPoints = alterPoints;
			this.dailyKills = dailyKills;
			this.weeklyKills = weeklyKills;
			this.lastKillTime = lastKillTime;
			this.lastResetTime = lastResetTime;
		}

		public synchronized void checkResets() {
			ZonedDateTime last = ServerTime.ofEpochMilli(lastResetTime > 0 ? lastResetTime : System.currentTimeMillis());
			ZonedDateTime now = ServerTime.now();

			boolean resetDaily = (last.getDayOfMonth() != now.getDayOfMonth() || last.getMonth() != now.getMonth() || last.getYear() != now.getYear());
			boolean resetWeekly = (last.get(java.time.temporal.IsoFields.WEEK_OF_WEEK_BASED_YEAR) != now.get(java.time.temporal.IsoFields.WEEK_OF_WEEK_BASED_YEAR)
				|| last.getYear() != now.getYear());

			if (resetDaily) {
				dailyKills = 0;
			}
			if (resetWeekly) {
				weeklyKills = 0;
			}
			if (resetDaily || resetWeekly) {
				lastResetTime = System.currentTimeMillis();
				getInstance().saveStats(this);
			}
		}
	}

	/**
	 * Ponto de entrada invocado quando o jogador clica no botão de espadas cruzadas (CM_SERVER_PVP_ACK).
	 */
	public void requestToggle(Player player) {
		if (player == null || !player.isOnline())
			return;

		if (player.isInCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS)) {
			deactivateFfa(player);
		} else {
			requestActivationWithConfirm(player);
		}
	}

	/**
	 * Emite a janela de confirmação de custo antes de iniciar a ativação do modo FFA.
	 */
	private void requestActivationWithConfirm(Player player) {
		String fail = checkConditions(player, true);
		if (fail != null) {
			PacketSendUtility.sendMessage(player, "[Secure Area] " + fail);
			return;
		}

		if (player.getAccount() == null)
			return;

		int accountId = player.getAccount().getId();
		long currentPoints = ParticipationPointsDAO.getPoints(accountId);
		if (currentPoints < FFA_COST_POINTS) {
			PacketSendUtility.sendMessage(player, "[Secure Area] Pontos insuficientes: " + FFA_COST_POINTS + " pts de Participação necessários (Saldo: " + currentPoints + ").");
			return;
		}

		RequestResponseHandler<Player> responseHandler = new RequestResponseHandler<>(player) {
			@Override
			public void acceptRequest(Player requester, Player responder) {
				activateFfa(responder);
			}

			@Override
			public void denyRequest(Player requester, Player responder) {
				PacketSendUtility.sendMessage(responder, "[Secure Area] Ativação do modo FFA cancelada pelo jogador.");
			}
		};

		boolean requested = player.getResponseRequester().putRequest(QUESTION_WINDOW_USE_COST_ID, responseHandler);
		if (requested) {
			PacketSendUtility.sendPacket(player, new SM_QUESTION_WINDOW(
				QUESTION_WINDOW_USE_COST_ID,
				0,
				0,
				"Pontos de Participação",
				String.valueOf(FFA_COST_POINTS)
			));
			PacketSendUtility.sendMessage(player, "[Secure Area] Deseja quebrar o pacto e ativar o Modo Altar FFA por " + FFA_COST_POINTS + " Pontos de Participação?");
		}
	}

	/**
	 * Aplica a cobrança de pontos e ativa o modo FFA do Altar.
	 */
	private void activateFfa(Player player) {
		if (player == null || !player.isOnline())
			return;

		String fail = checkConditions(player, false);
		if (fail != null) {
			PacketSendUtility.sendMessage(player, "[Secure Area] Falha ao ativar: " + fail);
			return;
		}

		int accountId = player.getAccount().getId();
		if (!ParticipationPointsDAO.tryDebitPoints(accountId, FFA_COST_POINTS)) {
			PacketSendUtility.sendMessage(player, "[Secure Area] Falha ao debitar " + FFA_COST_POINTS + " Pontos de Participação.");
			return;
		}

		player.setCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS);
		long cdEnd = System.currentTimeMillis() + FFA_COOLDOWN_MS;
		cooldownMap.put(accountId, cdEnd);

		AlterPlayerStats stats = getStats(player.getObjectId());
		stats.checkResets();

		// Envia SM_ALTER_INFO para o cliente nativo atualizar o HUD e o Livro de Eltar
		PacketSendUtility.sendPacket(player, new SM_ALTER_INFO(player.getObjectId(), cdEnd, stats.alterPoints));
		broadcastPlayerInfo(player);

		PacketSendUtility.sendMessage(player, "[Secure Area] Modo FFA/Altar ATIVADO! Custo: " + FFA_COST_POINTS + " pts. Duração/Cooldown: 1h.");
		log.info("[SecureArea] {} (account={}) ativou o modo FFA do Altar. {} pts debitados.", player.getName(), accountId, FFA_COST_POINTS);
		saveFfaRecord(accountId, true);
	}

	/**
	 * Desativa o modo FFA do Altar.
	 */
	private void deactivateFfa(Player player) {
		if (player == null)
			return;

		long remaining = getRemainingCooldownMs(player);
		if (remaining > 0) {
			long min = remaining / 60000;
			long sec = (remaining % 60000) / 1000;
			PacketSendUtility.sendMessage(player, "[Secure Area] Cooldown ativo para desativar: " + min + "m " + sec + "s.");
			return;
		}

		player.unsetCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS);
		int accountId = player.getAccount().getId();

		AlterPlayerStats stats = getStats(player.getObjectId());
		// Sincroniza término no cliente
		PacketSendUtility.sendPacket(player, new SM_ALTER_INFO(player.getObjectId(), 0L, stats.alterPoints));
		broadcastPlayerInfo(player);

		PacketSendUtility.sendMessage(player, "[Secure Area] Modo FFA/Altar DESATIVADO.");
		log.info("[SecureArea] {} (account={}) desativou o modo FFA do Altar.", player.getName(), accountId);
		saveFfaRecord(accountId, false);
	}

	/**
	 * Callback invocado quando ocorre uma baixa PvP entre jogadores.
	 */
	public void onPvpKill(Player winner, Player victim) {
		if (winner == null || victim == null)
			return;

		if (winner.isInCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS)) {
			AlterPlayerStats stats = getStats(winner.getObjectId());
			stats.checkResets();
			stats.alterKills++;
			stats.dailyKills++;
			stats.weeklyKills++;
			stats.alterPoints += FFA_POINTS_PER_KILL;
			stats.lastKillTime = System.currentTimeMillis();
			saveStats(stats);

			// Premiação por baixa de Altar: +25 Pontos de Participação
			ParticipationPointsDAO.addPoints(winner.getAccount().getId(), FFA_PARTICIPATION_REWARD_PER_KILL);

			// Atualiza a interface do cliente via SM_ALTER_INFO
			long cdEnd = getCooldownEndTime(winner);
			PacketSendUtility.sendPacket(winner, new SM_ALTER_INFO(winner.getObjectId(), cdEnd, stats.alterPoints));

			PacketSendUtility.sendMessage(winner, String.format(
				"[Altar] Inimigo abatido! +%d Pontos Eltar, +%d Pontos de Participação. Total de baixas: %d (Hoje: %d, Semana: %d).",
				FFA_POINTS_PER_KILL, FFA_PARTICIPATION_REWARD_PER_KILL, stats.alterKills, stats.dailyKills, stats.weeklyKills
			));

			checkRankMilestone(winner, stats.alterPoints);
		}
	}

	/**
	 * Valida e anuncia marcos de ranques alcançados segundo client_ffa_alter.xml.
	 */
	private void checkRankMilestone(Player player, int points) {
		String rankName = null;
		if (points == 100) {
			rankName = "Renegado (Ranque 1)";
		} else if (points >= 1250 && points < 1250 + FFA_POINTS_PER_KILL) {
			rankName = "Inquisidor (Ranque 2)";
		} else if (points >= 3825 && points < 3825 + FFA_POINTS_PER_KILL) {
			rankName = "Rebelde (Ranque 3)";
		} else if (points >= 6760 && points < 6760 + FFA_POINTS_PER_KILL) {
			rankName = "Legislador (Ranque 4)";
		} else if (points >= 9275 && points < 9275 + FFA_POINTS_PER_KILL) {
			rankName = "Anti-herói de Atreia (Ranque 5)";
		}

		if (rankName != null) {
			PacketSendUtility.sendMessage(player, "[Altar] Você alcançou o status de " + rankName + "! Verifique o Livro de Eltar.");
		}
	}

	/**
	 * Sincroniza as informações do Altar quando o jogador entra no mundo.
	 */
	public void onEnterWorld(Player player) {
		if (player == null)
			return;

		AlterPlayerStats stats = getStats(player.getObjectId());
		stats.checkResets();
		long cdEnd = getCooldownEndTime(player);
		PacketSendUtility.sendPacket(player, new SM_ALTER_INFO(player.getObjectId(), cdEnd, stats.alterPoints));
	}

	public void onLeaveWorld(Player player) {
		if (player == null)
			return;
		cancelPendingCharge(player);
		if (player.isInCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS)) {
			player.unsetCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS);
		}
	}

	public long getRemainingCooldownMs(Player player) {
		if (player == null || player.getAccount() == null)
			return 0L;
		Long cdEnd = cooldownMap.get(player.getAccount().getId());
		return cdEnd == null ? 0L : Math.max(0L, cdEnd - System.currentTimeMillis());
	}

	public long getCooldownEndTime(Player player) {
		if (player == null || player.getAccount() == null)
			return 0L;
		Long cdEnd = cooldownMap.get(player.getAccount().getId());
		return cdEnd == null ? 0L : cdEnd;
	}

	public int getAlterPoints(Player player) {
		if (player == null)
			return 0;
		return getStats(player.getObjectId()).alterPoints;
	}

	public int getAlterKills(Player player) {
		if (player == null)
			return 0;
		return getStats(player.getObjectId()).alterKills;
	}

	public boolean hasPendingCharge(Player player) {
		return player != null && pendingCharges.containsKey(player.getObjectId());
	}

	private boolean cancelPendingCharge(Player player) {
		Future<?> f = pendingCharges.remove(player.getObjectId());
		if (f != null && !f.isDone()) {
			f.cancel(false);
			return true;
		}
		return false;
	}

	private String checkConditions(Player player, boolean checkCooldown) {
		if (player.getLevel() < FFA_MIN_LEVEL)
			return "Nível mínimo " + FFA_MIN_LEVEL + " necessário.";
		if (player.isDead())
			return "Você está morto.";
		if (player.isCasting())
			return "Você está conjurando habilidade.";
		if (player.isInAttackMode())
			return "Você está em modo de ataque.";
		if (player.isFlying())
			return "Você está voando.";
		if (player.isInGlidingState())
			return "Você está planando.";
		if (player.isUsingFlightTransporterOrWindstream())
			return "Você está no windstream.";
		if (player.isTrading())
			return "Você está em negociação/loja.";
		if (player.getWorldId() >= 300000000)
			return "Não disponível em instâncias.";
		if (player.getInstanceId() > 2)
			return "Não disponível nesta instância.";
		if (checkCooldown) {
			long rem = getRemainingCooldownMs(player);
			if (rem > 0) {
				long min = rem / 60000;
				long sec = (rem % 60000) / 1000;
				return "Cooldown ativo: " + min + "m " + sec + "s.";
			}
		}
		return null;
	}

	private void broadcastPlayerInfo(Player player) {
		PacketSendUtility.broadcastPacket(player, new SM_PLAYER_INFO(player, false));
	}

	// -------------------------------------------------------------
	// Persistência em Banco de Dados
	// -------------------------------------------------------------

	public AlterPlayerStats getStats(int playerId) {
		return statsCache.computeIfAbsent(playerId, this::loadStats);
	}

	private AlterPlayerStats loadStats(int playerId) {
		String sql = "SELECT alter_kills, alter_points, daily_kills, weekly_kills, last_kill_time, last_reset_time " +
			"FROM player_alter_stats WHERE player_id = ?";
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement ps = con.prepareStatement(sql)) {
			ps.setInt(1, playerId);
			try (ResultSet rs = ps.executeQuery()) {
				if (rs.next()) {
					int kills = rs.getInt("alter_kills");
					int points = rs.getInt("alter_points");
					int daily = rs.getInt("daily_kills");
					int weekly = rs.getInt("weekly_kills");
					Timestamp lk = rs.getTimestamp("last_kill_time");
					Timestamp lr = rs.getTimestamp("last_reset_time");
					return new AlterPlayerStats(playerId, kills, points, daily, weekly,
						lk != null ? lk.getTime() : 0L,
						lr != null ? lr.getTime() : System.currentTimeMillis());
				}
			}
		} catch (SQLException e) {
			log.error("[SecureArea] Erro ao carregar estatísticas do jogador {}: {}", playerId, e.getMessage());
		}
		return new AlterPlayerStats(playerId, 0, 0, 0, 0, 0L, System.currentTimeMillis());
	}

	private void saveStats(AlterPlayerStats stats) {
		ThreadPoolManager.getInstance().execute(() -> {
			String sql = "INSERT INTO player_alter_stats (player_id, alter_kills, alter_points, daily_kills, weekly_kills, last_kill_time, last_reset_time) " +
				"VALUES (?, ?, ?, ?, ?, ?, ?) " +
				"ON DUPLICATE KEY UPDATE alter_kills = VALUES(alter_kills), alter_points = VALUES(alter_points), " +
				"daily_kills = VALUES(daily_kills), weekly_kills = VALUES(weekly_kills), " +
				"last_kill_time = VALUES(last_kill_time), last_reset_time = VALUES(last_reset_time)";
			try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement ps = con.prepareStatement(sql)) {
				ps.setInt(1, stats.playerId);
				ps.setInt(2, stats.alterKills);
				ps.setInt(3, stats.alterPoints);
				ps.setInt(4, stats.dailyKills);
				ps.setInt(5, stats.weeklyKills);
				ps.setTimestamp(6, stats.lastKillTime > 0 ? new Timestamp(stats.lastKillTime) : null);
				ps.setTimestamp(7, new Timestamp(stats.lastResetTime > 0 ? stats.lastResetTime : System.currentTimeMillis()));
				ps.executeUpdate();
			} catch (SQLException e) {
				log.error("[SecureArea] Erro ao salvar estatísticas do jogador {}: {}", stats.playerId, e.getMessage());
			}
		});
	}

	private void saveFfaRecord(int accountId, boolean activated) {
		ThreadPoolManager.getInstance().execute(() -> {
			String sql = "INSERT INTO player_secure_area_log (account_id, active, toggled_at) VALUES (?, ?, ?)";
			try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement ps = con.prepareStatement(sql)) {
				ps.setInt(1, accountId);
				ps.setBoolean(2, activated);
				ps.setTimestamp(3, new Timestamp(System.currentTimeMillis()));
				ps.executeUpdate();
			} catch (SQLException e) {
				log.debug("[SecureArea] Falha ao gravar log: {}", e.getMessage());
			}
		});
	}

	private void initTables() {
		String sqlLog = "CREATE TABLE IF NOT EXISTS `player_secure_area_log` (" +
			"`id` int(11) NOT NULL AUTO_INCREMENT," +
			"`account_id` int(11) NOT NULL," +
			"`active` tinyint(1) NOT NULL DEFAULT 0," +
			"`toggled_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP," +
			"PRIMARY KEY (`id`)," +
			"KEY `idx_account_id` (`account_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

		String sqlStats = "CREATE TABLE IF NOT EXISTS `player_alter_stats` (" +
			"`player_id` int(11) NOT NULL," +
			"`alter_kills` int(11) NOT NULL DEFAULT 0," +
			"`alter_points` int(11) NOT NULL DEFAULT 0," +
			"`daily_kills` int(11) NOT NULL DEFAULT 0," +
			"`weekly_kills` int(11) NOT NULL DEFAULT 0," +
			"`last_kill_time` timestamp NULL DEFAULT NULL," +
			"`last_reset_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP," +
			"PRIMARY KEY (`player_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

		try (Connection con = DatabaseFactory.getConnection();
			 Statement st = con.createStatement()) {
			st.executeUpdate(sqlLog);
			st.executeUpdate(sqlStats);
		} catch (SQLException e) {
			log.error("[SecureArea] Erro ao inicializar tabelas do Altar: {}", e.getMessage());
		}
	}
}
