package admincommands;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;

/**
 * Alias "//fix" para o comando FixSpawn.
 *
 * @author Lost Academy Team & Antigravity
 */
public class Fix extends AdminCommand {

	public Fix() {
		super("fix", "Corrige altura (Z) e direcao (Heading) de NPCs flutuando.");

		setSyntaxInfo(
			" - Corrige altura (Z) e direcao (Heading) do NPC para a do jogador (preserva X e Y).",
			"h - Corrige apenas a direcao (Heading) do NPC para a do jogador (preserva X, Y e Z)."
		);
	}

	@Override
	public void execute(Player admin, String... params) {
		FixSpawn.performFix(admin, params);
	}
}
