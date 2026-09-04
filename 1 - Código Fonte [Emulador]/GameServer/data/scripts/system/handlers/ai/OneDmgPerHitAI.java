package ai;

import com.aionemu.gameserver.ai2.AIName;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("onedmgperhit")
public class OneDmgPerHitAI extends NoActionAI
{
	@Override
	public int modifyDamage(int damage) {
		return 1;
	}
	
	@Override
	public int modifyOwnerDamage(int damage) {
		return 1;
	}
}