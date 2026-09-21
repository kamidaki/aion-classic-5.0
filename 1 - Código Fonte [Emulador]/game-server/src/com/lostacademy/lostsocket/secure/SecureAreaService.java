package com.lostacademy.lostsocket.secure;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Future;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.dao.ParticipationPointsDAO;
import com.aionemu.gameserver.model.gameobjects.player.CustomPlayerState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_PLAYER_INFO;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/** Secure Area FFA Service. @author Lost Academy Team + Durak */
public class SecureAreaService {

    private static final Logger log = LoggerFactory.getLogger(SecureAreaService.class);
    public static final long FFA_COST_POINTS = 100L;
    public static final long FFA_CHARGE_MS   = 10_000L;
    public static final long FFA_COOLDOWN_MS = 3_600_000L;
    public static final int  FFA_MIN_LEVEL   = 50;

    private static final ConcurrentHashMap<Integer, Long>      cooldownMap    = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<Integer, Future<?>> pendingCharges = new ConcurrentHashMap<>();

    private static final SecureAreaService instance = new SecureAreaService();
    public static SecureAreaService getInstance() { return instance; }
    private SecureAreaService() { initTable(); }

    public void requestToggle(Player player) {
        if (player == null || !player.isOnline()) return;
        if (cancelPendingCharge(player)) {
            PacketSendUtility.sendMessage(player, "[Secure Area] Ativacao cancelada.");
            broadcastPlayerInfo(player); return;
        }
        if (player.isInCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS)) { deactivateFfa(player); return; }
        activateFfa(player);
    }

    public void onLeaveWorld(Player player) {
        if (player == null) return;
        cancelPendingCharge(player);
        if (player.isInCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS))
            player.unsetCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS);
    }

    public long getRemainingCooldownMs(Player player) {
        if (player == null || player.getAccount() == null) return 0L;
        Long cdEnd = cooldownMap.get(player.getAccount().getId());
        return cdEnd == null ? 0L : Math.max(0L, cdEnd - System.currentTimeMillis());
    }

    public boolean hasPendingCharge(Player player) {
        return player != null && pendingCharges.containsKey(player.getObjectId());
    }

    private void activateFfa(Player player) {
        String fail = checkConditions(player, true);
        if (fail != null) { PacketSendUtility.sendMessage(player, "[Secure Area] " + fail); return; }
        int accountId = player.getAccount().getId();
        long pts = ParticipationPointsDAO.getPoints(accountId);
        if (pts < FFA_COST_POINTS) {
            PacketSendUtility.sendMessage(player, "[Secure Area] Insuficiente: " + FFA_COST_POINTS + " pts / Saldo: " + pts); return;
        }
        PacketSendUtility.sendMessage(player, "[Secure Area] Ativando FFA em 10s...");
        Future<?> f = ThreadPoolManager.getInstance().schedule(() -> {
            pendingCharges.remove(player.getObjectId());
            applyActivation(player, accountId);
        }, FFA_CHARGE_MS);
        pendingCharges.put(player.getObjectId(), f);
    }

    private void applyActivation(Player player, int accountId) {
        if (!player.isOnline()) return;
        String fail = checkConditions(player, false);
        if (fail != null) { PacketSendUtility.sendMessage(player, "[Secure Area] Interrompido: " + fail); return; }
        if (!ParticipationPointsDAO.tryDebitPoints(accountId, FFA_COST_POINTS)) {
            PacketSendUtility.sendMessage(player, "[Secure Area] Falha no debito."); return;
        }
        player.setCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS);
        cooldownMap.put(accountId, System.currentTimeMillis() + FFA_COOLDOWN_MS);
        PacketSendUtility.sendMessage(player, "[Secure Area] FFA ATIVADO! Custo: " + FFA_COST_POINTS + " pts.");
        broadcastPlayerInfo(player);
        log.info("[SecureArea] {} (account={}) FFA ON. {} pts.", player.getName(), accountId, FFA_COST_POINTS);
        saveFfaRecord(accountId, true);
    }

    private void deactivateFfa(Player player) {
        long remaining = getRemainingCooldownMs(player);
        if (remaining > 0) {
            long min = remaining / 60000; long sec = (remaining % 60000) / 1000;
            PacketSendUtility.sendMessage(player, "[Secure Area] Cooldown: " + min + "m " + sec + "s."); return;
        }
        player.unsetCustomState(CustomPlayerState.ENEMY_OF_ALL_PLAYERS);
        int accountId = player.getAccount().getId();
        cooldownMap.put(accountId, System.currentTimeMillis() + FFA_COOLDOWN_MS);
        PacketSendUtility.sendMessage(player, "[Secure Area] FFA DESATIVADO. Cooldown 1h.");
        broadcastPlayerInfo(player);
        log.info("[SecureArea] {} (acct={}) FFA OFF.", player.getName(), accountId);
        saveFfaRecord(accountId, false);
    }

    private boolean cancelPendingCharge(Player player) {
        Future<?> f = pendingCharges.remove(player.getObjectId());
        if (f != null && !f.isDone()) { f.cancel(false); return true; }
        return false;
    }

    private String checkConditions(Player player, boolean checkCooldown) {
        if (player.getLevel() < FFA_MIN_LEVEL) return "Nivel minimo " + FFA_MIN_LEVEL + " necessario.";
        if (player.isDead())                   return "Voce esta morto.";
        if (player.isCasting())                return "Voce esta usando habilidade.";
        if (player.isInAttackMode())           return "Voce esta em modo de ataque.";
        if (player.isFlying())                 return "Voce esta voando.";
        if (player.isInGlidingState())         return "Voce esta planando.";
        if (player.isUsingFlightTransporterOrWindstream()) return "Voce esta no windstream.";
        if (player.isTrading())                return "Voce esta em troca/loja.";
        if (player.getWorldId() >= 300000000)  return "Nao disponivel em instancias.";
        if (player.getInstanceId() > 2)        return "Nao disponivel nesta instancia.";
        if (checkCooldown) {
            long rem = getRemainingCooldownMs(player);
            if (rem > 0) {
                long min = rem / 60000; long sec = (rem % 60000) / 1000;
                return "Cooldown: " + min + "m " + sec + "s.";
            }
        }
        return null;
    }

    private void broadcastPlayerInfo(Player player) {
        PacketSendUtility.broadcastPacket(player, new SM_PLAYER_INFO(player, false));
    }

    private static final String INSERT_LOG =
        "INSERT INTO player_secure_area_log (account_id, active, toggled_at) VALUES (?, ?, ?)";

    private void saveFfaRecord(int accountId, boolean activated) {
        ThreadPoolManager.getInstance().execute(() -> {
            try (Connection con = DatabaseFactory.getConnection();
                 PreparedStatement ps = con.prepareStatement(INSERT_LOG)) {
                ps.setInt(1, accountId); ps.setBoolean(2, activated);
                ps.setTimestamp(3, new Timestamp(System.currentTimeMillis())); ps.executeUpdate();
            } catch (SQLException e) { log.debug("[SecureArea] Log falhou: {}", e.getMessage()); }
        });
    }

    private void initTable() {
        String sql = "CREATE TABLE IF NOT EXISTS player_secure_area_log (" +
            "id int(11) NOT NULL AUTO_INCREMENT," +
            "account_id int(11) NOT NULL," +
            "active tinyint(1) NOT NULL DEFAULT 0," +
            "toggled_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP," +
            "PRIMARY KEY (id)," +
            "KEY idx_account_id (account_id)" +
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4";
        try (Connection con = DatabaseFactory.getConnection();
             java.sql.Statement st = con.createStatement()) {
            st.executeUpdate(sql);
        } catch (SQLException e) { log.error("[SecureArea] Erro tabela: {}", e.getMessage()); }
    }
}
