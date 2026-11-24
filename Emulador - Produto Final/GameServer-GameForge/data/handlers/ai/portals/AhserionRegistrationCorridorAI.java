package ai.portals;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Npc;

/**
 * AI for Ahserion / Pangaea registration corridor portals using official client AI name 'ahserion_registration_corridor'.
 */
@AIName("ahserion_registration_corridor")
public class AhserionRegistrationCorridorAI extends PortalDialogAI {

	public AhserionRegistrationCorridorAI(Npc owner) {
		super(owner);
	}
}
