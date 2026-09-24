package admincommands;

import java.util.Arrays;
import java.util.List;

import com.aionemu.gameserver.dao.BlackCloudGoodsDAO;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.BlackCloudGoods;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.services.AdminService;
import com.aionemu.gameserver.services.mail.BlackCloudMailService;
import com.aionemu.gameserver.utils.ChatUtil;
import com.aionemu.gameserver.utils.Util;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;
import com.aionemu.gameserver.world.World;

/**
 * Entrega mercadorias no Black Cloud Mail (aba "Black Cloud" da janela do carteiro). A mercadoria é da conta: qualquer personagem dela
 * pode resgatar.
 */
public class BlackCloud extends AdminCommand {

	public BlackCloud() {
		super("blackcloud", "Delivers goods to the Black Cloud Mail of a player's account.");

		// @formatter:off
		setSyntaxInfo(
			"<player> <item link|ID> [count] [name] - Delivers the item as Black Cloud goods to the player's account (name defaults to \"<item name> (<count>)\").",
			"list <player> - Lists the pending Black Cloud goods of the player's account."
		);
		// @formatter:on
	}

	@Override
	public void execute(Player admin, String... params) {
		if (params.length < 2) {
			sendInfo(admin);
			return;
		}
		if ("list".equalsIgnoreCase(params[0])) {
			list(admin, Util.convertName(params[1]));
			return;
		}

		String playerName = Util.convertName(params[0]);
		int accountId = PlayerDAO.getAccountIdByName(playerName);
		if (accountId == 0) {
			sendInfo(admin, "Player " + playerName + " does not exist.");
			return;
		}
		int itemId = ChatUtil.getItemId(params[1]);
		ItemTemplate template = itemId == 0 ? null : DataManager.ITEM_DATA.getItemTemplate(itemId);
		if (template == null) {
			sendInfo(admin, "Invalid item.");
			return;
		}
		long count = params.length > 2 ? Long.parseLong(params[2]) : 1;
		if (count <= 0) {
			sendInfo(admin, "Invalid item count.");
			return;
		}
		if (!AdminService.getInstance().canOperate(admin, World.getInstance().getPlayer(playerName), itemId, "command //blackcloud"))
			return;

		String name = params.length > 3 ? String.join(" ", Arrays.copyOfRange(params, 3, params.length))
			: template.getName() + (count > 1 ? " (" + count + ")" : "");
		long goodsId = BlackCloudMailService.addGoods(accountId, name, itemId, count);
		if (goodsId == 0)
			sendInfo(admin, "Goods couldn't be delivered.");
		else
			sendInfo(admin, "Delivered Black Cloud goods " + goodsId + " (" + count + " x [item:" + itemId + "]) to the account of " + playerName + ".");
	}

	private void list(Player admin, String playerName) {
		int accountId = PlayerDAO.getAccountIdByName(playerName);
		if (accountId == 0) {
			sendInfo(admin, "Player " + playerName + " does not exist.");
			return;
		}
		List<BlackCloudGoods> goods = BlackCloudGoodsDAO.loadPending(accountId);
		StringBuilder sb = new StringBuilder("Black Cloud goods of " + playerName + "'s account: " + goods.size());
		for (BlackCloudGoods g : goods)
			sb.append("\n").append(g.id()).append(": ").append(g.name()).append(" - ").append(g.itemCount()).append(" x [item:").append(g.itemId()).append("]");
		sendInfo(admin, sb.toString());
	}
}
