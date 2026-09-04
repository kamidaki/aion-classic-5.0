package ai.instance.crucibleChallenge;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("barrel")
public class BarrelAI extends NpcAI
{
	@Override
	protected void handleDied() {
		super.handleDied();
		int npcId = 0;
		switch (getNpcId()) {
			case 217840: //Meat Barrel.
				npcId = 217841; //Wafer Thin Meet.
			break;
			case 218560: //Aether Barrel.
				npcId = 218561; //Aether Lump.
			break;
		}
		spawn(npcId, 1298.4448f, 1728.3262f, 316.8472f, (byte) 63);
		AIActions.deleteOwner(this);
	}
}