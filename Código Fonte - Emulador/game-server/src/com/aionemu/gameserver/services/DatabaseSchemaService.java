package com.aionemu.gameserver.services;

import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.dao.AccountQunaDAO;
import com.aionemu.gameserver.dao.LegionDonationDAO;
import com.aionemu.gameserver.dao.LegionMissionDAO;
import com.aionemu.gameserver.model.team.legion.LegionHistoryAction;
import com.aionemu.gameserver.dao.PlayerMorosDAO;
import com.aionemu.gameserver.dao.PlayerStorybookDAO;
import com.aionemu.gameserver.dao.PlayerWardrobeDAO;

/**
 * Serviço responsável por validar e inicializar automaticamente tabelas e colunas
 * necessárias no banco de dados durante o boot do GameServer.
 * Previne falhas de runtime e elimina a necessidade de intervenção manual em migrations simples.
 */
public class DatabaseSchemaService {

	private static final Logger log = LoggerFactory.getLogger(DatabaseSchemaService.class);

	public static void init() {
		log.info("DatabaseSchemaService: Verificando integridade das tabelas e colunas do GameServer...");
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTables(con);
			ensureColumns(con);
			log.info("DatabaseSchemaService: Verificação de esquema de banco de dados concluída com sucesso.");
		} catch (SQLException e) {
			log.error("DatabaseSchemaService: Erro ao verificar ou atualizar esquema do banco de dados!", e);
		}
	}

	private static void ensureTables(Connection con) {
		// 1. player_combat_talent_rewards (Classic 5.0)
		executeSql(con,
			"CREATE TABLE IF NOT EXISTS `player_combat_talent_rewards` (" +
			"  `player_id` INT NOT NULL," +
			"  `claimed_mask` INT UNSIGNED NOT NULL DEFAULT 0," +
			"  PRIMARY KEY (`player_id`)," +
			"  CONSTRAINT `player_combat_talent_rewards_player_fk` FOREIGN KEY (`player_id`)" +
			"    REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
		);

		// 2. player_siel_anvil (Classic 5.0 Bigorna de Siel)
		executeSql(con,
			"CREATE TABLE IF NOT EXISTS `player_siel_anvil` (" +
			"  `player_id` INT NOT NULL," +
			"  `recipe_id` INT NOT NULL," +
			"  `points` SMALLINT UNSIGNED NOT NULL DEFAULT 0," +
			"  PRIMARY KEY (`player_id`, `recipe_id`)," +
			"  CONSTRAINT `player_siel_anvil_player_fk` FOREIGN KEY (`player_id`)" +
			"    REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
		);

		// 3. account_blackcloud_goods (Classic 5.0 Black Cloud Mail: mercadorias da conta, S 0x10A/0x10C/0x10D)
		executeSql(con,
			"CREATE TABLE IF NOT EXISTS `account_blackcloud_goods` (" +
			"  `id` BIGINT NOT NULL AUTO_INCREMENT," +
			"  `account_id` INT NOT NULL," +
			"  `name` VARCHAR(100) NOT NULL," +
			"  `item_id` INT NOT NULL," +
			"  `item_count` BIGINT NOT NULL," +
			"  `register_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP," +
			"  `received_player_id` INT NULL DEFAULT NULL," +
			"  `received_time` TIMESTAMP NULL DEFAULT NULL," +
			"  PRIMARY KEY (`id`)," +
			"  KEY `account_pending` (`account_id`, `received_time`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
		);

		// 4. global_trade_listings (Classic 5.0 Global Auction House, C 0x114-0x117 / S 0x13C-0x145). O item fica no inventory com item_location 125.
		executeSql(con,
			"CREATE TABLE IF NOT EXISTS `global_trade_listings` (" +
			"  `id` BIGINT NOT NULL AUTO_INCREMENT," +
			"  `seller_id` INT NOT NULL," +
			"  `item_unique_id` INT NOT NULL," +
			"  `item_id` INT NOT NULL," +
			"  `item_count` BIGINT NOT NULL," +
			"  `price` BIGINT NOT NULL," +
			"  `currency` TINYINT NOT NULL," +
			"  `category` INT NOT NULL," +
			"  `register_fee` BIGINT NOT NULL DEFAULT 0," +
			"  `register_time` DATETIME NOT NULL," +
			"  `expire_time` DATETIME NOT NULL," +
			"  `state` VARCHAR(16) NOT NULL," +
			"  `buyer_id` INT NULL DEFAULT NULL," +
			"  `sold_time` DATETIME NULL DEFAULT NULL," +
			"  `sale_fee` BIGINT NOT NULL DEFAULT 0," +
			"  `collected_time` DATETIME NULL DEFAULT NULL," +
			"  PRIMARY KEY (`id`)," +
			"  KEY `state_seller` (`state`, `seller_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
		);

		// 5. player_moros (Classic 5.0 Moreth, Chronicle of Time: C 0x111 / S 0x169)
		executeSql(con, PlayerMorosDAO.CREATE_TABLE);

		// 6. player_storybook_items e player_storybook_finished (Classic 5.0 Book of Legends: C 0xDC/0xDD/0xE4 / S 0x14C-0x14E)
		executeSql(con, PlayerStorybookDAO.CREATE_ITEMS_TABLE);
		executeSql(con, PlayerStorybookDAO.CREATE_FINISHED_TABLE);

		// 7. player_wardrobe (Classic 5.0 Wardrobe: C 0xEE-0xFB / S 0x122-0x124)
		executeSql(con, PlayerWardrobeDAO.CREATE_TABLE);

		// 8. account_quna (Classic 5.0 Quna: saldo por conta, S 0x11B)
		executeSql(con, AccountQunaDAO.CREATE_TABLE);

		// legion_donation / player_legion_donation (produção de moedas da Legion 5.0, C_GUILD 0x13)
		executeSql(con, LegionDonationDAO.CREATE_LEGION_TABLE);
		executeSql(con, LegionDonationDAO.CREATE_PLAYER_TABLE);
		executeSql(con, LegionDonationDAO.CREATE_CRAFT_TABLE);

		// legion_mission / legion_growth (missões da Legion e crescimento, S 0x15C/0x15D/0x163/0x164)
		executeSql(con, LegionMissionDAO.CREATE_MISSION_TABLE);
		executeSql(con, LegionMissionDAO.CREATE_GROWTH_TABLE);

		// 9. player_participation_points (Pontos de Participação Lost Academy)
		executeSql(con,
			"CREATE TABLE IF NOT EXISTS `player_participation_points` (" +
			"  `account_id` INT NOT NULL," +
			"  `points` BIGINT NOT NULL DEFAULT '0'," +
			"  `last_update` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP," +
			"  PRIMARY KEY (`account_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
		);

		// 10. player_hits (Rastreamento de combos e histórico de golpes)
		executeSql(con,
			"CREATE TABLE IF NOT EXISTS `player_hits` (" +
			"  `account_id` INT NOT NULL," +
			"  `player_id` INT NOT NULL," +
			"  `cumulative_reward` INT NOT NULL DEFAULT '0'," +
			"  `better_amount_hits` INT NOT NULL DEFAULT '0'," +
			"  `daily_hits` INT NOT NULL DEFAULT '0'," +
			"  `weekly_hits` INT NOT NULL DEFAULT '0'," +
			"  `monthly_hits` INT NOT NULL DEFAULT '0'," +
			"  `year_hits` INT NOT NULL DEFAULT '0'," +
			"  `total_hits` INT NOT NULL DEFAULT '0'," +
			"  PRIMARY KEY (`account_id`, `player_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
		);

		// 11. player_secure_area_log (Registro e histórico de transições do Secure Area / FFA)
		executeSql(con,
			"CREATE TABLE IF NOT EXISTS `player_secure_area_log` (" +
			"  `id` INT NOT NULL AUTO_INCREMENT," +
			"  `player_id` INT NOT NULL," +
			"  `account_id` INT NOT NULL," +
			"  `player_name` VARCHAR(50) NOT NULL," +
			"  `action` VARCHAR(20) NOT NULL," +
			"  `world_id` INT NOT NULL," +
			"  `x` FLOAT NOT NULL," +
			"  `y` FLOAT NOT NULL," +
			"  `z` FLOAT NOT NULL," +
			"  `points_spent` INT NOT NULL DEFAULT 0," +
			"  `timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP," +
			"  PRIMARY KEY (`id`)," +
			"  KEY `idx_player` (`player_id`)," +
			"  KEY `idx_account` (`account_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
		);
	}

	private static void ensureColumns(Connection con) {
		// player_life_stats: colunas 'sp' e 'ep' para persistência de Revenant SP e Brawler EP/Ki
		if (!hasColumn(con, "player_life_stats", "sp")) {
			log.info("Adicionando coluna 'sp' na tabela player_life_stats...");
			executeSql(con, "ALTER TABLE `player_life_stats` ADD COLUMN `sp` int NOT NULL DEFAULT '0' AFTER `fp`;");
		}
		if (!hasColumn(con, "player_life_stats", "ep")) {
			log.info("Adicionando coluna 'ep' na tabela player_life_stats...");
			executeSql(con, "ALTER TABLE `player_life_stats` ADD COLUMN `ep` int NOT NULL DEFAULT '0' AFTER `sp`;");
		}
		// inventory: visual aplicado pelo Wardrobe 5.0 (C 0xFA), que o blob 0x0B marca e o Wardrobe remove
		if (!hasColumn(con, "inventory", "wardrobe_skin")) {
			log.info("Adicionando coluna 'wardrobe_skin' na tabela inventory...");
			executeSql(con, "ALTER TABLE `inventory` ADD COLUMN `wardrobe_skin` boolean NOT NULL DEFAULT '0' AFTER `item_skin`;");
		}
		// legion_craft: início e estado da produção de item da Legion (S 0x15A), 29/09
		if (!hasColumn(con, "legion_craft", "craft_start")) {
			log.info("Adicionando colunas de produção na tabela legion_craft...");
			executeSql(con, "ALTER TABLE `legion_craft` ADD COLUMN `craft_start` INT NOT NULL DEFAULT 0, ADD COLUMN `crafting` TINYINT NOT NULL DEFAULT 0;");
		}
		// legion_craft: favorito de produção (C_GUILD 0x16, C de cada receita no S 0x15A)
		if (!hasColumn(con, "legion_craft", "bookmark")) {
			log.info("Adicionando coluna 'bookmark' na tabela legion_craft...");
			executeSql(con, "ALTER TABLE `legion_craft` ADD COLUMN `bookmark` TINYINT NOT NULL DEFAULT 0;");
		}
		// legions: Legion Join Settings e Legion Activity (C_GUILD 0x10/0x17, S_GUILD_INFO)
		if (!hasColumn(con, "legions", "join_type")) {
			log.info("Adicionando colunas de entrada e atividade na tabela legions...");
			executeSql(con, "ALTER TABLE `legions` ADD COLUMN `join_type` TINYINT NOT NULL DEFAULT 0, ADD COLUMN `join_min_level` SMALLINT NOT NULL DEFAULT 0,"
				+ " ADD COLUMN `join_intro` VARCHAR(64) NOT NULL DEFAULT '', ADD COLUMN `campaign_activity` INT NOT NULL DEFAULT 0,"
				+ " ADD COLUMN `legion_activity` INT NOT NULL DEFAULT 0, ADD COLUMN `campaign_change_time` INT NOT NULL DEFAULT 0;");
		}
		// legion_history: ações de produção da 5.0 (aba 3), valores tirados do LegionHistoryAction
		String historyTypes = java.util.Arrays.stream(LegionHistoryAction.values()).map(a -> "'" + a.name() + "'")
			.collect(java.util.stream.Collectors.joining(","));
		if (!columnTypeContains(con, "legion_history", "history_type", "'" + LegionHistoryAction.CAMPAIGN_CHANGE.name() + "'")) {
			log.info("Atualizando os tipos de history_type na tabela legion_history...");
			executeSql(con, "ALTER TABLE `legion_history` MODIFY `history_type` enum(" + historyTypes + ") NOT NULL;");
		}
	}

	public static boolean hasTable(Connection con, String tableName) {
		try {
			DatabaseMetaData meta = con.getMetaData();
			try (ResultSet rs = meta.getTables(con.getCatalog(), null, tableName, new String[] {"TABLE"})) {
				if (rs.next()) {
					return true;
				}
			}
			// Fallback case-insensitive / sem catalog
			try (ResultSet rs = meta.getTables(null, null, tableName, new String[] {"TABLE"})) {
				return rs.next();
			}
		} catch (SQLException e) {
			log.warn("Erro ao checar existência da tabela {}: {}", tableName, e.getMessage());
			return false;
		}
	}

	private static boolean columnTypeContains(Connection con, String tableName, String columnName, String text) {
		try (java.sql.PreparedStatement stmt = con.prepareStatement(
			"SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND COLUMN_NAME = ?")) {
			stmt.setString(1, tableName);
			stmt.setString(2, columnName);
			try (ResultSet rs = stmt.executeQuery()) {
				return !rs.next() || rs.getString(1).contains(text);
			}
		} catch (SQLException e) {
			log.warn("Erro ao checar o tipo da coluna {} na tabela {}: {}", columnName, tableName, e.getMessage());
			return true;
		}
	}

	public static boolean hasColumn(Connection con, String tableName, String columnName) {
		try {
			DatabaseMetaData meta = con.getMetaData();
			try (ResultSet rs = meta.getColumns(con.getCatalog(), null, tableName, columnName)) {
				if (rs.next()) {
					return true;
				}
			}
			// Fallback sem catalog
			try (ResultSet rs = meta.getColumns(null, null, tableName, columnName)) {
				return rs.next();
			}
		} catch (SQLException e) {
			log.warn("Erro ao checar coluna {} na tabela {}: {}", columnName, tableName, e.getMessage());
			return false;
		}
	}

	private static void executeSql(Connection con, String sql) {
		try (Statement stmt = con.createStatement()) {
			stmt.executeUpdate(sql);
		} catch (SQLException e) {
			log.error("Falha ao executar DDL de auto-recuperação: " + sql, e);
		}
	}
}
