package com.aionemu.commons.database;

import java.sql.PreparedStatement;
import java.sql.SQLException;

/**
 * @author Lost Academy Team & Durak
 */
public interface ParamReadStH extends ReadStH {

	/**
	 * Enables coder to manually modify statement parameters.
	 * 
	 * @param stmt
	 * @throws SQLException
	 */
	public void setParams(PreparedStatement stmt) throws SQLException;
}
