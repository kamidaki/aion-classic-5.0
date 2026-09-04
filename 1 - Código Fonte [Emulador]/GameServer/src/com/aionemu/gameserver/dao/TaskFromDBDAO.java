package com.aionemu.gameserver.dao;

import com.aionemu.commons.database.dao.DAO;
import com.aionemu.gameserver.model.tasks.TaskFromDB;

import java.util.ArrayList;


public abstract class TaskFromDBDAO implements DAO {

	/**
	 * Return all tasks from DB
	 * 
	 * @return all tasks
	 */
	public abstract ArrayList<TaskFromDB> getAllTasks();

	/**
	 * Set the last activation to NOW()
	 */
	public abstract void setLastActivation(final int id);

	/**
	 * Returns class name that will be uses as unique identifier for all DAO classes
	 * 
	 * @return class name
	 */
	@Override
	public final String getClassName() {
		return TaskFromDBDAO.class.getName();
	}
}
