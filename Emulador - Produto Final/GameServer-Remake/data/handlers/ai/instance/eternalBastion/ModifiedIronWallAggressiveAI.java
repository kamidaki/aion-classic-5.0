package ai.instance.eternalBastion;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Npc;

/**
 * AI for Eternal Bastion aggressive NPCs using official Korean client AI name 'modified_iron_wall_aggressive'.
 */
@AIName("modified_iron_wall_aggressive")
public class ModifiedIronWallAggressiveAI extends EternalBastionAggressiveNpcAI {

	public ModifiedIronWallAggressiveAI(Npc owner) {
		super(owner);
	}
}
