package admincommands;

import com.aionemu.gameserver.dao.AccountQunaDAO;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.AdminService;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.player.QunaService;
import com.aionemu.gameserver.utils.ChatUtil;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.Util;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;
import com.aionemu.gameserver.world.World;

/**
 * @author Lost Academy Team & Durak
 */
public class Add extends AdminCommand {

	public Add() {
		super("add", "Adds Kinah, Quna or items to a player.");

		// @formatter:off
		setSyntaxInfo(
			"kinah <amount> - Adds the specified amount of Kinah to your inventory.",
			"quna <amount> - Adds the specified amount of Quna to your account.",
			"<item link|ID> [count] - Adds the specified item(s) to your inventory.",
			"<player> kinah <amount> - Adds the specified amount of Kinah to the player's inventory.",
			"<player> quna <amount> - Adds the specified amount of Quna to the player's account.",
			"<player> <item link|ID> [count] - Adds the specified item(s) to the player's inventory."
		);
		// @formatter:on
	}

	@Override
	public void execute(Player player, String... params) {
		if (params.length < 1) {
			sendInfo(player);
			return;
		}

		int index = 0;
		Player receiver = player;
		boolean isKinah = false;
		boolean isQuna = false;

		if ("Kinah".equalsIgnoreCase(params[index])) {
			isKinah = true;
		} else if ("Quna".equalsIgnoreCase(params[index])) {
			isQuna = true;
		}

		int itemId = isKinah ? ItemId.KINAH : isQuna ? QunaService.QUNA_ITEM_ID : ChatUtil.getItemId(params[index]);
		if (itemId == 0) {
			String playerName = Util.convertName(params[index]);
			receiver = World.getInstance().getPlayer(playerName);
			if (receiver == null) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_NO_SUCH_USER(playerName));
				return;
			}
			if (++index < params.length) {
				if ("Kinah".equalsIgnoreCase(params[index])) {
					isKinah = true;
				} else if ("Quna".equalsIgnoreCase(params[index])) {
					isQuna = true;
				}
				itemId = isKinah ? ItemId.KINAH : isQuna ? QunaService.QUNA_ITEM_ID : ChatUtil.getItemId(params[index]);
			}
		}

		long itemCount;
		try {
			itemCount = params.length > ++index ? Long.parseLong(params[index]) : 1;
		} catch (NumberFormatException e) {
			sendInfo(player, "Invalid count.");
			return;
		}

		if (itemCount <= 0) {
			sendInfo(player, "Invalid count.");
			return;
		}

		if (isQuna) {
			int accountId = receiver.getClientConnection() != null ? receiver.getClientConnection().getAccount().getId()
				: PlayerDAO.getAccountIdByName(receiver.getName());
			if (accountId == 0 || !QunaService.addToAccount(accountId, itemCount)) {
				sendInfo(player, "Quna couldn't be added.");
				return;
			}
			long newBalance = 0;
			try {
				newBalance = AccountQunaDAO.load(accountId);
			} catch (Exception ignored) {
			}
			if (player != receiver) {
				sendInfo(player, "You gave " + itemCount + " Quna to " + receiver.getName() + " (new balance: " + newBalance + ").");
				sendInfo(receiver, "You received " + itemCount + " Quna from " + player.getName() + " (new balance: " + newBalance + ").");
			} else {
				sendInfo(player, "You added " + itemCount + " Quna to your account (new balance: " + newBalance + ").");
			}
			return;
		}

		ItemTemplate itemTemplate;
		if (itemId == 0 || (itemTemplate = DataManager.ITEM_DATA.getItemTemplate(itemId)) == null) {
			sendInfo(player, "Invalid item.");
			return;
		}

		if (itemId == ItemId.KINAH ? receiver.getInventory().getKinah() + itemCount < 0 : itemCount / itemTemplate.getMaxStackCount() > 126) {
			sendInfo(player, "Invalid item count.");
			return;
		}

		if (!AdminService.getInstance().canOperate(player, receiver, itemId, "command //add"))
			return;

		long notAddedCount = ItemService.addItem(receiver, itemId, itemCount, true);
		if (notAddedCount == 0) {
			if (player != receiver) {
				sendInfo(player, "You gave " + itemCount + " x [item:" + itemId + "] to " + receiver.getName() + ".");
				sendInfo(receiver, "You received " + itemCount + " x [item:" + itemId + "] from " + player.getName() + ".");
			}
		} else {
			sendInfo(player, "Item couldn't be added");
		}
	}
}
