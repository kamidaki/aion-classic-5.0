package consolecommands;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.chathandlers.ConsoleCommand;

/**
 * Godstone proc rate, for testing. The GM panel sends this command. The value is a multiplier on the proc chance of
 * every godstone (see GodStone.tryActivate), not a chance itself: a godstone with probability 100 (10%) procs always at
 * ratio 10 or higher. It is not enough on its own, since one godstone only rolls once per evaluation cooldown, which is
 * why the cooldown can be set here too.
 * <p>
 * Both are runtime only, on the whole server, and go back to config/main/custom.properties on the next restart.
 *
 * @author Lost Academy Team & Durak
 */
public class Set_proc_activation_ratio extends ConsoleCommand {

	public Set_proc_activation_ratio() {
		super("set_proc_activation_ratio", "Sets the godstone proc rate.");

		// @formatter:off
		setSyntaxInfo(
			" - Shows the current rate and evaluation cooldown.",
			"<ratio> - Multiplies the proc chance of every godstone (1 = server default, 0 = never, 100 = always).",
			"cooldown <milliseconds> - Wait between proc rolls of one godstone (0 = roll on every hit)."
		);
		// @formatter:on
	}

	@Override
	public void execute(Player admin, String... params) {
		if (params.length == 0) {
			showCurrent(admin);
			return;
		}

		if ("cooldown".equalsIgnoreCase(params[0])) {
			if (params.length != 2) {
				sendInfo(admin);
				return;
			}
			int millis;
			try {
				millis = Integer.parseInt(params[1]);
			} catch (NumberFormatException e) {
				sendInfo(admin, "<" + params[1] + " is not a whole number>");
				return;
			}
			if (millis < 0) {
				sendInfo(admin, "<The cooldown cannot be negative>");
				return;
			}
			CustomConfig.GODSTONE_EVALUATION_COOLDOWN_MILLIS = millis;
			showCurrent(admin);
			return;
		}

		float ratio;
		try {
			ratio = Float.parseFloat(params[0].endsWith("%") ? params[0].substring(0, params[0].length() - 1) : params[0]);
		} catch (NumberFormatException e) {
			sendInfo(admin, "<" + params[0] + " is not a number>");
			return;
		}
		if (ratio < 0) {
			sendInfo(admin, "<The ratio cannot be negative>");
			return;
		}
		CustomConfig.GODSTONE_ACTIVATION_RATE = ratio;
		showCurrent(admin);
	}

	private void showCurrent(Player admin) {
		PacketSendUtility.sendMessage(admin, "Godstone proc ratio: " + CustomConfig.GODSTONE_ACTIVATION_RATE + " (1 = server default), one roll every "
			+ CustomConfig.GODSTONE_EVALUATION_COOLDOWN_MILLIS + " ms. Until the next server restart.");
	}
}
