package com.aionemu.commons.database;

import java.sql.PreparedStatement;
import java.sql.SQLException;

/**
 * @author Lost Academy Team & Durak
 */
public interface IUStH {

	/**
	 * Enables coder to manually modify statement or batch. Must execute batch or statement manually. Automatically recycles connection.
	 * 
	 * @param stmt
	 * @throws SQLException
	 */
	void handleInsertUpdate(PreparedStatement stmt) throws SQLException;
}
