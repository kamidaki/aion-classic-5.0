package com.aionemu.gameserver.services;

import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;

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
