package com.aionemu.gameserver.services.mail;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.BlackCloudGoodsDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.BlackCloudGoods;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.serverpackets.SM_NPSHOP_GOODS_COUNT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_NPSHOP_GOODS_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_NPSHOP_GOODS_RECV;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.item.ItemService.ItemUpdatePredicate;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;

/**
 * Black Cloud Mail (NPShop 5.0): mercadorias da conta, resgatadas pela aba "Black Cloud" da janela do carteiro.
 * <p>
 * Fluxo da captura oficial 06_Sistemas_Novos_Black_Cloud_Mail_5.0_2026-09-14:
 * <ul>
 * <li>C 0x9D C_SA_GOODSLIST → S 0x10C S_RESPONSE_NPSHOP_GOODS_LIST; o cliente pede a contagem em seguida.</li>
 * <li>C 0xAA C_REQUEST_NPSHOP_GOODS_COUNT → S 0x10A S_NPSHOP_GOODS_COUNT.</li>
 * <li>C 0x9E C_SA_CONFIRMGOODS [Q id] → S 0x1B/0x1D com motivo 0x7A e S 0x10D S_RESPONSE_NPSHOP_GOODS_RECV [Q id][D 0].</li>
 * </ul>
 * A contagem também sai na autenticação da conta, antes da lista de personagens, e é por conta: os 4 goods da captura já aparecem ali.
 */
public final class BlackCloudMailService {

	public static final int NAME_MAX_LENGTH = 100;

	private static final Logger log = LoggerFactory.getLogger("MAIL_LOG");
	private static final ItemUpdatePredicate GOODS_ADD = new ItemUpdatePredicate(ItemAddType.NPSHOP_GOODS, ItemUpdateType.INC_NPSHOP_GOODS);

	private BlackCloudMailService() {
	}

	public static int getGoodsCount(int accountId) {
		return BlackCloudGoodsDAO.countPending(accountId);
	}

	public static boolean hasGoods(Player player) {
		return getGoodsCount(player.getAccount().getId()) > 0;
	}

	public static void sendGoodsCount(Player player) {
		PacketSendUtility.sendPacket(player, new SM_NPSHOP_GOODS_COUNT(getGoodsCount(player.getAccount().getId())));
	}

	/**
	 * Uma página só: se a fila não couber num pacote, o resto aparece quando o jogador resgatar as primeiras.
	 */
	public static void sendGoodsList(Player player) {
		List<BlackCloudGoods> goods = BlackCloudGoodsDAO.loadPending(player.getAccount().getId());
		int bodySize = SM_NPSHOP_GOODS_LIST.STATIC_BODY_SIZE;
		int shown = 0;
		for (BlackCloudGoods g : goods) {
			bodySize += SM_NPSHOP_GOODS_LIST.bodySize(g);
			if (bodySize > AionServerPacket.MAX_USABLE_PACKET_BODY_SIZE)
				break;
			shown++;
		}
		PacketSendUtility.sendPacket(player, new SM_NPSHOP_GOODS_LIST(goods.subList(0, shown)));
	}

	public static void receiveGoods(Player player, long goodsId) {
		if (!player.isSpawned() || player.isTrading()) {
			reply(player, goodsId, SM_NPSHOP_GOODS_RECV.FAILURE);
			return;
		}
		Storage inventory = player.getInventory();
		synchronized (inventory) {
			BlackCloudGoods goods = BlackCloudGoodsDAO.loadPending(player.getAccount().getId(), goodsId);
			ItemTemplate template = goods == null ? null : DataManager.ITEM_DATA.getItemTemplate(goods.itemId());
			if (template == null) {
				if (goods != null)
					log.warn("Black Cloud goods " + goods + " points to an item without template");
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_INGAMESHOP_INVALID_GOODS());
				reply(player, goodsId, SM_NPSHOP_GOODS_RECV.FAILURE);
				return;
			}
			if (!ItemService.hasInventorySpace(inventory, template, goods.itemCount())) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_UI_INVENTORY_FULL());
				reply(player, goodsId, SM_NPSHOP_GOODS_RECV.FAILURE);
				return;
			}
			if (!BlackCloudGoodsDAO.markReceived(goods, player.getObjectId())) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_INGAMESHOP_INVALID_GOODS());
				reply(player, goodsId, SM_NPSHOP_GOODS_RECV.FAILURE);
				return;
			}
			long notAdded = ItemService.addItem(player, goods.itemId(), goods.itemCount(), false, GOODS_ADD);
			log.info("Player " + player.getName() + " received Black Cloud goods " + goods.id() + " [" + goods.name() + "]: item " + goods.itemId()
				+ " x" + (goods.itemCount() - notAdded));
			if (notAdded > 0) {
				// devolve só o que não entrou, como mercadoria nova, para não duplicar o que já foi para o inventário
				long restoredId = BlackCloudGoodsDAO.insert(goods.accountId(), goods.name(), goods.itemId(), notAdded);
				log.warn("Black Cloud goods " + goods.id() + ": " + notAdded + " of item " + goods.itemId() + " did not fit, returned as goods "
					+ restoredId);
			}
			reply(player, goodsId, SM_NPSHOP_GOODS_RECV.SUCCESS);
		}
	}

	/**
	 * Entrega uma mercadoria à conta. Se um personagem dela estiver no mundo, recebe o aviso de compra e a contagem nova.
	 *
	 * @return id da mercadoria, ou 0 se não foi gravada
	 */
	public static long addGoods(int accountId, String name, int itemId, long itemCount) {
		if (accountId <= 0 || itemCount <= 0 || name == null || name.isBlank() || DataManager.ITEM_DATA.getItemTemplate(itemId) == null)
			return 0;
		if (name.length() > NAME_MAX_LENGTH)
			name = name.substring(0, NAME_MAX_LENGTH);
		long goodsId = BlackCloudGoodsDAO.insert(accountId, name, itemId, itemCount);
		if (goodsId == 0)
			return 0;
		log.info("Black Cloud goods " + goodsId + " [" + name + "] (item " + itemId + " x" + itemCount + ") delivered to account " + accountId);
		Player online = findInWorld(accountId);
		if (online != null) {
			PacketSendUtility.sendPacket(online, SM_SYSTEM_MESSAGE.STR_POSTMAN_NOTIFY_CASH());
			sendGoodsCount(online);
		}
		return goodsId;
	}

	private static Player findInWorld(int accountId) {
		for (Player player : World.getInstance().getAllPlayers())
			if (player.getAccount().getId() == accountId)
				return player;
		return null;
	}

	private static void reply(Player player, long goodsId, int result) {
		PacketSendUtility.sendPacket(player, new SM_NPSHOP_GOODS_RECV(goodsId, result));
	}
}
