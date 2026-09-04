package ai.instance.padmarashkaCave;

import com.aionemu.commons.utils.Rnd;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.skillengine.SkillEngine;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Padmarashka_Eggs")
public class Padmarashka_EggsAI extends NpcAI
{
	private void applySoldierWrath(final Npc npc) {
		SkillEngine.getInstance().getSkill(npc, 20176, 60, npc).useNoAnimationSkill(); //Hatching Soldier's Wrath.
	}
	
	@Override
	protected void handleDied() {
		//Neonate Drakan.
		switch (Rnd.get(1, 5)) {
			case 1:
			    applySoldierWrath((Npc) spawn(282615, getOwner().getX(), getOwner().getY(), getOwner().getZ(), (byte) getOwner().getHeading()));
			break;
			case 2:
			    applySoldierWrath((Npc) spawn(282616, getOwner().getX(), getOwner().getY(), getOwner().getZ(), (byte) getOwner().getHeading()));
			break;
			case 3:
			    applySoldierWrath((Npc) spawn(282617, getOwner().getX(), getOwner().getY(), getOwner().getZ(), (byte) getOwner().getHeading()));
			break;
			case 4:
			    applySoldierWrath((Npc) spawn(282618, getOwner().getX(), getOwner().getY(), getOwner().getZ(), (byte) getOwner().getHeading()));
			break;
			case 5:
			    applySoldierWrath((Npc) spawn(282619, getOwner().getX(), getOwner().getY(), getOwner().getZ(), (byte) getOwner().getHeading()));
			break;
		}
		super.handleDied();
		AIActions.deleteOwner(this);
	}
}