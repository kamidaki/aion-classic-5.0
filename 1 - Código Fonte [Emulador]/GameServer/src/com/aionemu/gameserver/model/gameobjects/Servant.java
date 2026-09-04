package com.aionemu.gameserver.model.gameobjects;

import com.aionemu.gameserver.controllers.NpcController;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.npc.NpcTemplate;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import org.apache.commons.lang.StringUtils;

public class Servant extends SummonedObject<Creature>
{
	private NpcObjectType objectType;
	
	public Servant(int objId, NpcController controller, SpawnTemplate spawnTemplate, NpcTemplate objectTemplate, int level) {
		super(objId, controller, spawnTemplate, objectTemplate, level);
	}
	
	@Override
	public final boolean isEnemy(Creature creature) {
		return getCreator().isEnemy(creature);
	}
	
	@Override
	public boolean isEnemyFrom(Player player) {
		return getCreator() != null && getCreator().isEnemyFrom(player);
	}
	
	@Override
	public NpcObjectType getNpcObjectType() {
		return objectType;
	}
	
	public void setNpcObjectType(NpcObjectType objectType) {
		this.objectType = objectType;
	}
	
	@Override
	public String getMasterName() {
		return StringUtils.EMPTY;
	}
}