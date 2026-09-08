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
 * @author Lost Academy Team & Durak
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
		if (DatabaseConfig.DATABASE_CONNECTIONS_MIN > 0 && DatabaseConfig.DATABASE_CONNECTIONS_MIN <= DatabaseConfig.DATABASE_CONNECTIONS_MAX) {
			config.setMinimumIdle(DatabaseConfig.DATABASE_CONNECTIONS_MIN);
		}
		config.setConnectionTimeout(DatabaseConfig.DATABASE_TIMEOUT);
		if (DatabaseConfig.DATABASE_MAX_LIFETIME >= 30000) {
			config.setMaxLifetime(DatabaseConfig.DATABASE_MAX_LIFETIME);
		}
		if (DatabaseConfig.DATABASE_IDLE_TIMEOUT >= 10000) {
			config.setIdleTimeout(DatabaseConfig.DATABASE_IDLE_TIMEOUT);
		}
		if (DatabaseConfig.DATABASE_KEEPALIVE >= 30000) {
			config.setKeepaliveTime(DatabaseConfig.DATABASE_KEEPALIVE);
		}

		// Performance optimizations for MySQL / MariaDB over network
		config.addDataSourceProperty("cachePrepStmts", "true");
		config.addDataSourceProperty("prepStmtCacheSize", "500");
		config.addDataSourceProperty("prepStmtCacheSqlLimit", "2048");
		config.addDataSourceProperty("useServerPrepStmts", "true");
		config.addDataSourceProperty("useLocalSessionState", "true");
		config.addDataSourceProperty("rewriteBatchedStatements", "true");
		config.addDataSourceProperty("cacheResultSetMetadata", "true");
		config.addDataSourceProperty("cacheServerConfiguration", "true");
		config.addDataSourceProperty("elideSetAutoCommits", "true");
		config.addDataSourceProperty("maintainTimeStats", "false");
		config.addDataSourceProperty("tcpKeepAlive", "true");
		config.addDataSourceProperty("tcpNoDelay", "true");

		dataSource = new HikariDataSource(config);

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

	private DatabaseFactory() {
	}
}
