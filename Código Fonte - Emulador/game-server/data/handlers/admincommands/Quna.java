package admincommands;

import com.aionemu.gameserver.dao.AccountQunaDAO;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.services.player.QunaService;
import com.aionemu.gameserver.utils.Util;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;

/**
 * Saldo de Quna da conta de um personagem. O saldo é da conta: todos os personagens dela usam o mesmo.
 */
public class Quna extends AdminCommand {

	public Quna() {
		super("quna", "Shows or changes the Quna balance of a player's account.");

		// @formatter:off
		setSyntaxInfo(
			"<player> - Shows the Quna balance of the player's account.",
			"<player> <amount> - Adds Quna to the player's account (a negative amount removes it, never below 0)."
		);
		// @formatter:on
	}

	@Override
	public void execute(Player admin, String... params) {
		if (params.length < 1) {
			sendInfo(admin);
			return;
		}
		String playerName = Util.convertName(params[0]);
		int accountId = PlayerDAO.getAccountIdByName(playerName);
		if (accountId == 0) {
			sendInfo(admin, "Player " + playerName + " does not exist.");
			return;
		}
		if (params.length > 1) {
			long amount;
			try {
				amount = Long.parseLong(params[1]);
			} catch (NumberFormatException e) {
				sendInfo(admin, "Invalid amount.");
				return;
			}
			if (amount == 0 || !QunaService.addToAccount(accountId, amount)) {
				sendInfo(admin, "The Quna balance of " + playerName + "'s account couldn't be changed by " + amount + ".");
				return;
			}
		}
		try {
			sendInfo(admin, "Quna of " + playerName + "'s account (" + accountId + "): " + AccountQunaDAO.load(accountId));
		} catch (Exception e) {
			sendInfo(admin, "The Quna balance couldn't be read.");
		}
	}
}
