package ai;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Npc;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("onedmgperhit")
public class OneDmgPerHitAI extends NoActionAI
{
	public OneDmgPerHitAI() {
		super();
	}

	public OneDmgPerHitAI(Npc owner) {
		super(owner);
	}

	@Override
	public int modifyDamage(int damage) {
		return 1;
	}
	
	@Override
	public int modifyOwnerDamage(int damage) {
		return 1;
	}
}