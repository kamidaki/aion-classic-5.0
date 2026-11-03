package playercommands;

import admincommands.FixSpawn;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.services.CommandsAccessService;
import com.aionemu.gameserver.utils.chathandlers.PlayerCommand;

/**
 * Permite a execucao do FixSpawn via comando de ponto ".fix".
 * Restrito estritamente a membros staff / administradores com acesso de GM.
 *
 * @author Lost Academy Team & Antigravity
 */
public class PlayerFix extends PlayerCommand {

	public PlayerFix() {
		super("fix", "Corrige altura (Z) e direcao (Heading) de NPCs flutuando.");

		setSyntaxInfo(
			" - Corrige altura (Z) e direcao (Heading) do NPC para a do jogador (preserva X e Y).",
			"h - Corrige apenas a direcao (Heading) do NPC para a do jogador (preserva X, Y e Z)."
		);
	}

	@Override
	public boolean validateAccess(Player player) {
		if (player == null) {
			return false;
		}
		boolean hasAccess = player.isStaff() || CommandsAccessService.hasAccess(player.getObjectId(), getAliasForLevel());
		if (!hasAccess) {
			sendInfo(player, "<Voce precisa ser Administrador para usar este comando>");
			return false;
		}
		return true;
	}

	@Override
	public void execute(Player player, String... params) {
		FixSpawn.performFix(player, params);
	}
}
