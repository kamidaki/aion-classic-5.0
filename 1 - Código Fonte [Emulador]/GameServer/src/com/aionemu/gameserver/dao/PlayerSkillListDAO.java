package com.aionemu.gameserver.dao;

import com.aionemu.commons.database.dao.DAO;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.skill.PlayerSkillList;

import java.sql.Timestamp;

public abstract class PlayerSkillListDAO implements DAO
{
	@Override
	public final String getClassName() {
		return PlayerSkillListDAO.class.getName();
	}
	public abstract PlayerSkillList loadSkillList(int playerId);
	public abstract boolean storeSkills(Player player);
}