package com.aionemu.commons.database;

import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * @author Lost Academy Team & Durak
 */
public interface ReadStH {

	/**
	 * Allows coder to read data after query execution. Automatically recycles connection and closes ResultSet.
	 * 
	 * @param rset
	 * @throws SQLException
	 */
	public void handleRead(ResultSet rset) throws SQLException;
}
