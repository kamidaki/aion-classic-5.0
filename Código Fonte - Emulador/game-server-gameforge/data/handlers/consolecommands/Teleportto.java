package consolecommands;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.chathandlers.ChatProcessor;
import com.aionemu.gameserver.utils.chathandlers.ConsoleCommand;

import admincommands.GoTo;

/**
 * @author Lost Academy Team & Durak
 */
public class Teleportto extends ConsoleCommand {

	public Teleportto() {
		super("teleportto", "Teleports you to regions by name.");
	}

	@Override
	public String getSyntaxInfo() {
		GoTo goTo = ChatProcessor.getInstance().getCommand(GoTo.class);
		return goTo.getSyntaxInfo().replace(goTo.getAliasWithPrefix(), getAliasWithPrefix());
	}

	@Override
	public void execute(Player admin, String... params) {
		ChatProcessor.getInstance().getCommand(GoTo.class).execute(admin, params);
	}
}
