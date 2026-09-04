package ai.instance.darkPoeta;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Marabata_Controller")
public class Marabata_ControllerAI extends NpcAI
{
	@Override
	public void think() {
	}
	
	@Override
    protected void handleSpawned() {
        super.handleSpawned();
		switch (getNpcId()) {
			///Marabata Of Strength.
			case 700439:
			case 700440:
			case 700441:
				AIActions.targetCreature(Marabata_ControllerAI.this, getPosition().getWorldMapInstance().getNpc(214849));
				AIActions.useSkill(Marabata_ControllerAI.this, 18110);
				AIActions.useSkill(Marabata_ControllerAI.this, 18556);
		    break;
			///Marabata Of Aether.
			case 700442:
			case 700443:
			case 700444:
				AIActions.targetCreature(Marabata_ControllerAI.this, getPosition().getWorldMapInstance().getNpc(214850));
				AIActions.useSkill(Marabata_ControllerAI.this, 18110);
				AIActions.useSkill(Marabata_ControllerAI.this, 18556);
		    break;
			///Marabata Of Poisoning.
			case 700445:
			case 700446:
			case 700447:
				AIActions.targetCreature(Marabata_ControllerAI.this, getPosition().getWorldMapInstance().getNpc(214851));
				AIActions.useSkill(Marabata_ControllerAI.this, 18110);
				AIActions.useSkill(Marabata_ControllerAI.this, 18556);
		    break;
		}
    }
	
	@Override
	public boolean isMoveSupported() {
		return false;
	}
}