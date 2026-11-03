package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import com.aionemu.commons.database.DatabaseFactory;

/**
 * Saldo de Quna da conta (account_quna). Toda mudança é uma soma ou subtração atômica no banco, para uma loja web poder creditar com um INSERT
 * ... ON DUPLICATE KEY UPDATE enquanto o jogador está logado.
 */
public class AccountQunaDAO {

	public static final String CREATE_TABLE = "CREATE TABLE IF NOT EXISTS `account_quna` (" +
		"  `account_id` INT NOT NULL," +
		"  `quna` BIGINT NOT NULL DEFAULT 0," +
		"  PRIMARY KEY (`account_id`)" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
	private static final String SELECT_QUERY = "SELECT `quna` FROM `account_quna` WHERE `account_id`=?";
	private static final String ADD_QUERY = "INSERT INTO `account_quna` (`account_id`, `quna`) VALUES (?, ?) ON DUPLICATE KEY UPDATE `quna` = `quna` + VALUES(`quna`)";
	private static final String DECREASE_QUERY = "UPDATE `account_quna` SET `quna` = `quna` - ? WHERE `account_id`=? AND `quna` >= ?";

	/**
	 * @return o saldo, 0 para conta sem linha
	 */
	public static long load(int accountId) throws SQLException {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(SELECT_QUERY)) {
			stmt.setInt(1, accountId);
			try (ResultSet rs = stmt.executeQuery()) {
				return rs.next() ? rs.getLong(1) : 0;
			}
		}
	}

	public static void add(int accountId, long amount) throws SQLException {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(ADD_QUERY)) {
			stmt.setInt(1, accountId);
			stmt.setLong(2, amount);
			stmt.executeUpdate();
		}
	}

	/**
	 * @return false se o saldo não cobre o valor; nada muda nesse caso
	 */
	public static boolean tryDecrease(int accountId, long amount) throws SQLException {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(DECREASE_QUERY)) {
			stmt.setLong(1, amount);
			stmt.setInt(2, accountId);
			stmt.setLong(3, amount);
			return stmt.executeUpdate() == 1;
		}
	}
}
