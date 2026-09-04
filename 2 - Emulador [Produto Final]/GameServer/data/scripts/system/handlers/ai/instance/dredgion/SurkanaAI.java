package ai.instance.dredgion;

import ai.OneDmgPerHitAI;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("surkana")
public class SurkanaAI extends OneDmgPerHitAI
{
	@Override
	protected void handleAttack(Creature creature) {
		super.handleAttack(creature);
		checkForSupport(creature);
	}
	
	private void checkForSupport(Creature creature) {
		for (VisibleObject object : getKnownList().getKnownObjects().values()) {
			if (object instanceof Npc && isInRange(object, 20)) {
				((Npc) object).getAi().onCreatureEvent(AIEventType.CREATURE_AGGRO, creature);
			}
		}
	}
}