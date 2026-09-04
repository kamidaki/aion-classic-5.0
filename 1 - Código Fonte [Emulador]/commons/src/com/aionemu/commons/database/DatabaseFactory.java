package com.aionemu.commons.database;

import java.sql.Connection;
import java.sql.SQLException;

import javax.sql.DataSource;

import org.slf4j.LoggerFactory;

import com.aionemu.commons.configs.DatabaseConfig;
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.pool.HikariPool;

/**
 * This file is used for creating a pool of connections for the server.<br>
 * It utilizes database.properties and creates a pool of connections and automatically recycles them when closed.<br>
 * 
 */
public class DatabaseFactory {

	/**
	 * Connection Pool holds all connections - Idle or Active
	 */
	private static DataSource dataSource;

	public synchronized static void init() {
		if (dataSource != null) {
			return;
		}

		HikariConfig config = new HikariConfig();
		config.setJdbcUrl(DatabaseConfig.DATABASE_URL);
		config.setUsername(DatabaseConfig.DATABASE_USER);
		config.setPassword(DatabaseConfig.DATABASE_PASSWORD);
		config.setMaximumPoolSize(DatabaseConfig.DATABASE_CONNECTIONS_MAX);
		config.setConnectionTimeout(DatabaseConfig.DATABASE_TIMEOUT);

		dataSource = new HikariDataSource(config);

		try (Connection c = getConnection()) {
			java.sql.DatabaseMetaData dmd = c.getMetaData();
			databaseName = dmd.getDatabaseProductName();
			databaseMajorVersion = dmd.getDatabaseMajorVersion();
			databaseMinorVersion = dmd.getDatabaseMinorVersion();
		} catch (Exception e) {
			LoggerFactory.getLogger(DatabaseFactory.class).error("Error reading database metadata", e);
		}
	}

	private static String databaseName = "MySQL";
	private static int databaseMajorVersion = 5;
	private static int databaseMinorVersion = 0;

	public static String getDatabaseName() {
		return databaseName;
	}

	public static int getDatabaseMajorVersion() {
		return databaseMajorVersion;
	}

	public static int getDatabaseMinorVersion() {
		return databaseMinorVersion;
	}

	public static synchronized void shutdown() {
		if (dataSource instanceof HikariDataSource hikari) {
			try {
				hikari.close();
			} catch (Exception e) {
				LoggerFactory.getLogger(DatabaseFactory.class).warn("Failed to shutdown DatabaseFactory", e);
			}
		}
		dataSource = null;
	}

	/**
	 * @return An active connection from the {@link HikariPool connection pool}
	 * @see HikariDataSource#getConnection()
	 */
	public static Connection getConnection() throws SQLException {
		Connection con = dataSource.getConnection();

		if (!con.getAutoCommit()) {
			LoggerFactory.getLogger(DatabaseFactory.class).error("Connection was not in auto-commit mode.", new IllegalStateException());
			con.setAutoCommit(true);
		}

		return con;
	}

	public static void close(java.sql.Statement st, Connection con) {
		close(st);
		close(con);
	}

	public static void close(java.sql.Statement st) {
		if (st == null) {
			return;
		}
		try {
			if (!st.isClosed()) {
				st.close();
			}
		} catch (SQLException e) {
			LoggerFactory.getLogger(DatabaseFactory.class).error("Can't close Statement", e);
		}
	}

	public static void close(Connection con) {
		if (con == null) {
			return;
		}
		try {
			if (!con.getAutoCommit()) {
				con.setAutoCommit(true);
			}
		} catch (SQLException e) {
			LoggerFactory.getLogger(DatabaseFactory.class).error("Failed to set autocommit to true while closing connection: ", e);
		}
		try {
			con.close();
		} catch (SQLException e) {
			LoggerFactory.getLogger(DatabaseFactory.class).error("DatabaseFactory: Failed to close database connection!", e);
		}
	}

	private DatabaseFactory() {
	}
}

