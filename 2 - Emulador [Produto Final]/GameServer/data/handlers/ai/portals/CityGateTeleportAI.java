package ai.portals;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.animations.TeleportAnimation;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.services.teleport.TeleportService;
import ai.GeneralNpcAI;

/**
 * AI for Gatekeeper NPCs at capital entrance maps:
 * - 730648 (Sanctum Gate 110030000 -> Sanctum 110010000)
 * - 730649 (Pandaemonium Entrance 120030000 -> Pandaemonium 120010000)
 *
 * Prevents client error "load fail! LC1a_LGuard_GUIDE_01.html" when interacting
 * with the gate soldiers by directly teleporting the player into the city.
 */
@AIName("city_gate_teleport")
public class CityGateTeleportAI extends GeneralNpcAI {

	public CityGateTeleportAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleDialogStart(Player player) {
		if (getNpcId() == 730648) {
			// Sanctum Gate (110030000) -> Sanctum (110010000)
			TeleportService.teleportTo(player, 110010000, 1313.25f, 1512.011f, 568.107f, (byte) 58, TeleportAnimation.FADE_OUT_BEAM);
		} else if (getNpcId() == 730649) {
			// Pandaemonium Entrance (120030000) -> Pandaemonium (120010000)
			TeleportService.teleportTo(player, 120010000, 1657.5f, 1398.7f, 194.7f, (byte) 0, TeleportAnimation.FADE_OUT_BEAM);
		} else {
			super.handleDialogStart(player);
		}
	}
}
