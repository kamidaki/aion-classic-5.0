package consolecommands;

import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.chathandlers.ConsoleCommand;

/**
 * @author Lost Academy Team & Durak
 */
public class Classup extends ConsoleCommand {

	public Classup() {
		super("classup", "Promotes a players class.");

		setSyntaxInfo("<class> - Promotes your target's class to the one specified (defaults to your character, if no player is targeted).");
	}

	@Override
	public void execute(Player admin, String... params) {
	}
}
