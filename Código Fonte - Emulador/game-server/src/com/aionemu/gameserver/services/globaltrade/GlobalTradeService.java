package com.aionemu.gameserver.services.globaltrade;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Predicate;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.GlobalTradeConfig;
import com.aionemu.gameserver.dao.GlobalTradeDAO;
import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.ItemStoneListDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.LetterType;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing.State;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_AVG_PRICE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_BUY;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_CANCEL;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_COLLECT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_COMMIT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_HISTORY;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_MYLIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_SALESLOG;
import com.aionemu.gameserver.network.aion.serverpackets.SM_GLOBAL_TRADE_STATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.AdminService;
import com.aionemu.gameserver.services.item.ItemFactory;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemDeleteType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.mail.SystemMailService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.utils.idfactory.IDFactory;
import com.aionemu.gameserver.world.World;

/**
 * Global Auction House do Classic 5.0: anúncios do servidor inteiro, sem separação de raça. O protocolo está nas classes SM_GLOBAL_TRADE_*
 * e CM_GLOBAL_TRADE_*; os padrões de taxa, limite e nível no GlobalTradeConfig.
 * <p>
 * Só a moeda kinah funciona. O anúncio em Luna (moeda 0, inclusive a aba de venda de kinah) é recusado, porque o emulador não tem a Luna
 * da loja.
 * <p>
 * Toda mudança de anúncio passa pelo lock deste serviço. O item anunciado fica no inventory com o local GLOBAL_TRADE e o vendedor como dono;
 * as operações gravam a linha do anúncio antes de mexer em item e kinah, e gravam o item logo depois, para uma queda do servidor não
 * duplicar item.
 */
public final class GlobalTradeService {

	private static final Logger log = LoggerFactory.getLogger(GlobalTradeService.class);

	// client_strings_msg 5.0
	private static final int MSG_BUY = 1300785; // STR_MSG_BUY_ITEM_MULTI: %1 %0 comprados
	private static final int MSG_CANNOT_REGISTER = 1401777; // STR_MSG_WORLD_VENDOR_ITEM_CANNOT_BE_REGISTER
	private static final int MSG_FULL_BASKET = 1401780; // STR_MSG_WORLD_VENDOR_FULL_BASKET
	private static final int MSG_SOLD = 1401782; // STR_MSG_WORLD_VENDOR_SOLD_OUT (%0)
	private static final int MSG_REVENUE_WAITING = 1401783; // STR_MSG_WORLD_VENDOR_CONNECT_SALES_SUCCESS
	private static final int MSG_BELOW_STANDARD = 1401784; // STR_MSG_WORLD_VENDOR_BELOW_STANDARD
	private static final int MSG_NOT_ENOUGH_QUNA = 1401788; // STR_MSG_WORLD_VENDOR_NOT_ENOUGH_QUNA
	private static final int MSG_REGISTERED = 1401789; // STR_MSG_WORLD_VENDOR_REGISTRATION_STACK: %1x %0
	private static final int MSG_CANCELED = 1401790; // STR_MSG_WORLD_VENDOR_REGISTRATION_CANCLE
	private static final int MSG_COLLECTED = 1401793; // STR_MSG_WORLD_VENDOR_ACCOUNT_END: %0 itens
	private static final int MSG_ERROR = 1401794; // STR_MSG_WORLD_VENDOR_USED_ERROR
	private static final int MSG_RESTRICTED = 1401795; // STR_MSG_WORLD_VENDOR_MASTER_KEY
	private static final int MSG_ALREADY_SOLD = 1401835; // STR_MSG_WORLD_VENDOR_SOLD_OUT_WARNING
	private static final int MSG_CANNOT_USE_NOW = 1401853; // STR_MSG_WORLD_VENDOR_CAN_NOT_USE
	/** STR_MSG_WORLD_VENDOR_REMOVE_CHARACTER_CANCEL: personagem com anúncio ou receita não pode ser apagado */
	public static final int MSG_DELETE_CHARACTER = 1401855;

	/** A página do C_GLOBAL_TRADE_LIST anda de 9 em 9 e a resposta traz até 18, em pacotes de no máximo 15 (captura). */
	private static final int PAGE_STEP = 9, PAGE_SIZE = 18, PACKET_ENTRIES = 15;
	/** STR_UI_VENDOR_WORLD_INCOME_TIP: o histórico de receitas cobre os últimos 28 dias. */
	private static final long HISTORY_MILLIS = 28L * 24 * 60 * 60 * 1000;
	private static final long EXPIRE_CHECK_MILLIS = 60_000, EXPIRE_RETRY_MILLIS = 60 * 60_000;
	private static final String MAIL_SENDER = "Auction House";
	private static final String MAIL_TITLE = "Item not sold";
	private static final String MAIL_BODY = "Your Auction House listing has expired. The item has been returned.";

	private final Map<Long, GlobalTradeListing> listings = new ConcurrentHashMap<>();
	private final Map<Long, Long> expireRetry = new HashMap<>();

	public static GlobalTradeService getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private GlobalTradeService() {
		List<Item> items = InventoryDAO.loadItemsAt(StorageType.GLOBAL_TRADE);
		ItemStoneListDAO.load(items);
		Map<Integer, Item> itemsById = new HashMap<>();
		for (Item item : items)
			itemsById.put(item.getObjectId(), item);
		for (GlobalTradeListing listing : GlobalTradeDAO.load(System.currentTimeMillis() - HISTORY_MILLIS)) {
			if (listing.getState() == State.LISTED) {
				Item item = itemsById.remove(listing.getItemUniqueId());
				if (item == null) {
					log.warn("{} sem o item {} no local GLOBAL_TRADE: anúncio cancelado", listing, listing.getItemUniqueId());
					listing.setState(State.CANCELED);
					GlobalTradeDAO.update(listing);
					continue;
				}
				listing.setItem(item);
			}
			listings.put(listing.getId(), listing);
		}
		for (Item orphan : itemsById.values())
			log.warn("Item {} ({} x{}) no local GLOBAL_TRADE sem anúncio à venda", orphan.getObjectId(), orphan.getItemId(), orphan.getItemCount());
		ThreadPoolManager.getInstance().scheduleAtFixedRate(this::checkExpired, EXPIRE_CHECK_MILLIS, EXPIRE_CHECK_MILLIS);
		log.info("Global Auction House: {} anúncios à venda, {} vendas a receber, {} itens anunciáveis",
			count(l -> l.getState() == State.LISTED), count(l -> l.getState() == State.SOLD), DataManager.GLOBAL_TRADE_DATA.size());
	}

	// ------------------------------------------------------------------ consultas

	/** C 0x10C, ao abrir a janela. */
	public void sendState(Player player) {
		if (isEnabled(player))
			PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_STATE(GlobalTradeConfig.WEEKLY_KINAH_LIMIT));
	}

	/**
	 * C_GLOBAL_TRADE_LIST. Com {@code itemIds} (busca por nome, resolvida no cliente) a categoria é ignorada.
	 */
	public void sendList(Player player, int sort, int page, int category, GlobalTradeCurrency currency, byte[] requestTail, Set<Integer> itemIds) {
		if (!isEnabled(player) || currency == null || page == 0xFFFF) // página 0xFFFF logo depois da compra: o oficial não responde
			return;
		boolean search = !itemIds.isEmpty();
		List<GlobalTradeListing> found = listings.values().stream()
			.filter(l -> l.getState() == State.LISTED && l.getCurrency() == currency
				&& (search ? itemIds.contains(l.getItemId()) : inCategory(l.getCategory(), category)))
			.sorted(comparator(sort)).toList();
		int from = Math.min(found.size(), page * PAGE_STEP);
		List<GlobalTradeListing> shown = found.subList(from, Math.min(found.size(), from + PAGE_SIZE));
		Map<Integer, Long> averages = new HashMap<>();
		List<SM_GLOBAL_TRADE_LIST.Entry> entries = new ArrayList<>();
		for (GlobalTradeListing listing : shown)
			entries.add(new SM_GLOBAL_TRADE_LIST.Entry(listing,
				averages.computeIfAbsent(listing.getItemId(), id -> averageUnitPriceX100(id, currency))));
		int packets = Math.max(1, (entries.size() + PACKET_ENTRIES - 1) / PACKET_ENTRIES);
		for (int i = 0; i < packets; i++) {
			List<SM_GLOBAL_TRADE_LIST.Entry> part = entries.subList(i * PACKET_ENTRIES, Math.min(entries.size(), (i + 1) * PACKET_ENTRIES));
			PacketSendUtility.sendPacket(player,
				new SM_GLOBAL_TRADE_LIST(found.size(), search, page, category, i == 0, i == packets - 1, requestTail, part));
		}
	}

	/** C_GLOBAL_TRADE_MYLIST [D moeda]: anúncios à venda do jogador nessa moeda, ao escolher a moeda na aba de registro. */
	public void sendMyList(Player player, GlobalTradeCurrency currency) {
		if (isEnabled(player) && currency != null)
			PacketSendUtility.sendPacket(player,
				new SM_GLOBAL_TRADE_MYLIST(currency, mine(player.getObjectId(), State.LISTED, currency, Comparator.comparingLong(GlobalTradeListing::getId))));
	}

	/**
	 * C_GLOBAL_TRADE_AVG_PRICE, ao pôr um item na aba de registro: menor e maior preço unitário dos anúncios à venda daquele item na moeda.
	 * Capturas: 19.400/19.400 com um anúncio só em Luna, 0/0 sem anúncio, 200.000/200.000.000 e 200.000/20.000.000 em kinah.
	 */
	public void sendAveragePrice(Player player, int itemObjId, GlobalTradeCurrency currency) {
		Item item = player.getInventory().getItemByObjId(itemObjId);
		if (!isEnabled(player) || currency == null || item == null)
			return;
		var prices = listings.values().stream()
			.filter(l -> l.getState() == State.LISTED && l.getItemId() == item.getItemId() && l.getCurrency() == currency)
			.mapToLong(l -> l.getPrice() / l.getCount()).summaryStatistics();
		PacketSendUtility.sendPacket(player,
			new SM_GLOBAL_TRADE_AVG_PRICE(itemObjId, prices.getCount() == 0 ? 0 : prices.getMin(), prices.getCount() == 0 ? 0 : prices.getMax(), currency));
	}

	/**
	 * C_GLOBAL_TRADE_SALESLOG: vendas com receita a receber naquela moeda. O cliente pede as moedas 0 e 1 em todo login, de qualquer nível
	 * (168 pedidos em 45 capturas), e o oficial responde sem mensagem.
	 */
	public void sendSalesLog(Player player, GlobalTradeCurrency currency) {
		if (!GlobalTradeConfig.ENABLE || currency == null)
			return;
		List<GlobalTradeListing> sold = mine(player.getObjectId(), State.SOLD, currency, Comparator.comparingLong(GlobalTradeListing::getSoldTime));
		PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_SALESLOG(currency, false, sum(sold, GlobalTradeListing::getRevenue), sold.size(), sold));
	}

	/** C_GLOBAL_TRADE_HISTORY e depois do COLLECT: vendas recebidas nos últimos 28 dias naquela moeda, mais recente primeiro. */
	public void sendHistory(Player player, GlobalTradeCurrency currency) {
		if (!GlobalTradeConfig.ENABLE || currency == null)
			return;
		long since = System.currentTimeMillis() - HISTORY_MILLIS;
		List<GlobalTradeListing> history = mine(player.getObjectId(), State.COLLECTED, currency,
			Comparator.comparingLong(GlobalTradeListing::getCollectedTime).reversed()).stream().filter(l -> l.getCollectedTime() >= since).toList();
		PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_HISTORY(currency, sum(history, GlobalTradeListing::getRevenue), history.size(), history));
	}

	/**
	 * No login o oficial manda o S_GLOBAL_TRADE_SALESLOG das duas moedas como aviso (valor bruto das vendas a receber, sem entradas) e, com
	 * venda a receber, STR_MSG_WORLD_VENDOR_CONNECT_SALES_SUCCESS. O cliente pede as duas moedas em seguida.
	 */
	public void onPlayerLogin(Player player) {
		if (!GlobalTradeConfig.ENABLE)
			return;
		boolean waiting = false;
		for (GlobalTradeCurrency currency : List.of(GlobalTradeCurrency.LUNA, GlobalTradeCurrency.KINAH)) {
			List<GlobalTradeListing> sold = mine(player.getObjectId(), State.SOLD, currency, Comparator.comparingLong(GlobalTradeListing::getSoldTime));
			PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_SALESLOG(currency, true, sum(sold, GlobalTradeListing::getPrice), 0, List.of()));
			waiting |= !sold.isEmpty();
		}
		if (waiting)
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REVENUE_WAITING));
	}

	// ------------------------------------------------------------------ operações

	/**
	 * C_GLOBAL_TRADE_COMMIT. Anúncio de parte de uma pilha cria um item novo com a quantidade anunciada; a pilha fica com o resto.
	 */
	public void commit(Player player, int itemObjId, long price, long count, GlobalTradeCurrency currency) {
		if (!canTrade(player))
			return;
		synchronized (this) {
			Storage inventory = player.getInventory();
			Item item = inventory.getItemByObjId(itemObjId);
			if (currency != GlobalTradeCurrency.KINAH || item == null || item.isEquipped() || item.isSoulBound() || item.getExpireTime() > 0
				|| item.getTemporaryExchangeTime() > 0 || !DataManager.GLOBAL_TRADE_DATA.canRegister(item.getItemId(), currency)) {
				log.info("[GLOBAL_TRADE] {} não pode anunciar o objeto {} em {}", player.getName(), itemObjId, currency);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_CANNOT_REGISTER));
				return;
			}
			if (count <= 0 || count > item.getItemCount() || price <= 0 || price > GlobalTradeConfig.MAX_PRICE) {
				log.warn("[GLOBAL_TRADE] {} mandou anúncio inválido: objeto {} x{} por {}", player.getName(), itemObjId, count, price);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ERROR));
				return;
			}
			if (count(l -> l.getSellerId() == player.getObjectId() && l.getState() == State.LISTED) >= GlobalTradeConfig.MAX_LISTINGS) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_FULL_BASKET));
				return;
			}
			long fee = price * GlobalTradeConfig.REGISTER_FEE_PERMYRIAD / 10000;
			if (inventory.getKinah() < fee) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_NOT_ENOUGH_MONEY());
				return;
			}
			if (!AdminService.getInstance().canOperate(player, null, item, "global trade"))
				return;

			boolean wholeStack = count == item.getItemCount();
			Item listed = wholeStack ? item : ItemFactory.newItem(item.getItemId(), count);
			long now = System.currentTimeMillis();
			long expire = now + GlobalTradeConfig.LISTING_DAYS * 24L * 60 * 60 * 1000;
			int category = DataManager.GLOBAL_TRADE_DATA.getCategory(item.getItemId());
			long id = GlobalTradeDAO.insert(player.getObjectId(), listed.getObjectId(), item.getItemId(), count, price, currency, category, fee, now, expire);
			if (id == 0) {
				if (!wholeStack)
					IDFactory.getInstance().releaseObjectIds(List.of(listed));
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ERROR));
				return;
			}

			// ordem da captura: taxa (0x1D motivo 0x9C), saída do item, mensagem, S_GLOBAL_TRADE_COMMIT
			inventory.decreaseKinah(fee, ItemUpdateType.DEC_KINAH_GLOBAL_TRADE_FEE);
			List<Item> toStore = new ArrayList<>(List.of(listed));
			if (inventory.getKinahItem() != null)
				toStore.add(inventory.getKinahItem());
			if (wholeStack) {
				inventory.remove(item); // sai do cubo sem virar DELETED: a mesma linha do inventory passa para o local GLOBAL_TRADE
				ItemPacketService.sendItemDeletePacket(player, StorageType.CUBE, item, ItemDeleteType.GLOBAL_TRADE_REGISTER); // 0x1C + 0x81
			} else {
				inventory.decreaseItemCount(item, count, ItemUpdateType.DEC_ITEM_SPLIT);
				toStore.add(item);
			}
			listed.setItemLocation(StorageType.GLOBAL_TRADE.getId());
			InventoryDAO.store(toStore, player.getObjectId());

			GlobalTradeListing listing = new GlobalTradeListing(id, player.getObjectId(), listed.getObjectId(), listed.getItemId(), count, price,
				currency, category, fee, now, expire, State.LISTED, 0, 0, 0, 0);
			listing.setItem(listed);
			listings.put(id, listing);
			log.info("[GLOBAL_TRADE] {} anunciou {} (taxa {})", player.getName(), listing, fee);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REGISTERED, nameOf(listing.getItemId()), String.valueOf(count)));
			PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_COMMIT(listing));
		}
	}

	/** C_GLOBAL_TRADE_BUY: a compra leva o anúncio inteiro. */
	public void buy(Player player, long listingId) {
		if (!canTrade(player))
			return;
		synchronized (this) {
			GlobalTradeListing listing = listings.get(listingId);
			if (listing == null || listing.getState() != State.LISTED) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ALREADY_SOLD));
				return;
			}
			if (listing.getCurrency() != GlobalTradeCurrency.KINAH) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_NOT_ENOUGH_QUNA));
				return;
			}
			if (listing.getSellerId() == player.getObjectId()) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_VENDOR_CAN_NOT_BUY_MY_REGISTER_ITEM());
				return;
			}
			Storage inventory = player.getInventory();
			Item item = listing.getItem();
			if (inventory.isFull(item.getItemTemplate().getExtraInventoryId())) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_FULL_INVENTORY());
				return;
			}
			if (inventory.getKinah() < listing.getPrice()) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_NOT_ENOUGH_MONEY());
				return;
			}
			listing.markSold(player.getObjectId(), System.currentTimeMillis(), listing.getPrice() * GlobalTradeConfig.SALE_FEE_PERMYRIAD / 10000);
			if (!GlobalTradeDAO.update(listing)) {
				listing.unmarkSold();
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ERROR));
				return;
			}
			listing.setItem(null);

			// ordem da captura: kinah (0x1D motivo 0x13C), mensagem, S_GLOBAL_TRADE_BUY, S_ADD_INVENTORY (cabeçalho 0x98)
			inventory.decreaseKinah(listing.getPrice(), ItemUpdateType.DEC_KINAH_GLOBAL_TRADE_BUY);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_BUY, nameOf(listing.getItemId()), String.valueOf(listing.getCount())));
			PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_BUY(listing.getId(), listing.getCount()));
			inventory.add(item, ItemAddType.GLOBAL_TRADE_BUY);
			InventoryDAO.store(List.of(item, inventory.getKinahItem()), player.getObjectId());
			log.info("[GLOBAL_TRADE] {} comprou {}", player.getName(), listing);

			Player seller = World.getInstance().getPlayer(listing.getSellerId());
			if (seller != null)
				PacketSendUtility.sendPacket(seller, new SM_SYSTEM_MESSAGE(MSG_SOLD, nameOf(listing.getItemId())));
		}
	}

	/** C_GLOBAL_TRADE_COLLECT [D moeda]: recebe todas as vendas daquela moeda. */
	public void collect(Player player, GlobalTradeCurrency currency) {
		if (!canTrade(player) || currency != GlobalTradeCurrency.KINAH)
			return;
		synchronized (this) {
			List<GlobalTradeListing> sold = mine(player.getObjectId(), State.SOLD, currency, Comparator.comparingLong(GlobalTradeListing::getSoldTime));
			if (sold.isEmpty())
				return;
			long now = System.currentTimeMillis(), revenue = 0;
			int collected = 0;
			for (GlobalTradeListing listing : sold) {
				listing.markCollected(now);
				if (GlobalTradeDAO.update(listing)) {
					revenue += listing.getRevenue();
					collected++;
				} else {
					listing.unmarkCollected();
				}
			}
			if (collected == 0) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ERROR));
				return;
			}
			// ordem da captura: kinah (0x1D motivo 0x13D), mensagem, S_GLOBAL_TRADE_COLLECT, histórico (0x145)
			player.getInventory().increaseKinah(revenue, ItemUpdateType.INC_KINAH_GLOBAL_TRADE_COLLECT);
			InventoryDAO.store(player.getInventory().getKinahItem(), player.getObjectId());
			log.info("[GLOBAL_TRADE] {} recebeu {} de {} vendas", player.getName(), revenue, collected);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_COLLECTED, String.valueOf(collected)));
			PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_COLLECT(collected));
			sendHistory(player, currency);
		}
	}

	/** C_GLOBAL_TRADE_CANCEL [Q anúncio]: o item volta ao cubo. Só vale para anúncio à venda do próprio jogador. */
	public void cancel(Player player, long listingId) {
		if (!canTrade(player))
			return;
		synchronized (this) {
			GlobalTradeListing listing = listings.get(listingId);
			if (listing == null || listing.getSellerId() != player.getObjectId() || listing.getState() != State.LISTED) {
				log.info("[GLOBAL_TRADE] {} pediu cancelamento de anúncio {} que não é dele ou não está à venda", player.getName(), listingId);
				return;
			}
			Storage inventory = player.getInventory();
			Item item = listing.getItem();
			if (inventory.isFull(item.getItemTemplate().getExtraInventoryId())) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_FULL_INVENTORY());
				return;
			}
			listing.setState(State.CANCELED);
			if (!GlobalTradeDAO.update(listing)) {
				listing.setState(State.LISTED);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ERROR));
				return;
			}
			listings.remove(listingId);
			listing.setItem(null);
			// ordem da captura: S_ADD_INVENTORY (cabeçalho 0x9E), mensagem, S_GLOBAL_TRADE_CANCEL; o cliente pede o STATE em seguida
			inventory.add(item, ItemAddType.GLOBAL_TRADE_CANCEL);
			InventoryDAO.store(item, player.getObjectId());
			log.info("[GLOBAL_TRADE] {} cancelou {}", player.getName(), listing);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_CANCELED));
			PacketSendUtility.sendPacket(player, new SM_GLOBAL_TRADE_CANCEL(listingId));
		}
	}

	/** Anúncio vencido volta ao vendedor pelo correio, com o próprio item (encanto e pedras preservados). */
	private void checkExpired() {
		long now = System.currentTimeMillis();
		synchronized (this) {
			for (GlobalTradeListing listing : List.copyOf(listings.values())) {
				if (listing.getState() != State.LISTED || listing.getExpireTime() > now || expireRetry.getOrDefault(listing.getId(), 0L) > now)
					continue;
				if (!SystemMailService.sendMail(MAIL_SENDER, listing.getSellerId(), MAIL_TITLE, MAIL_BODY, listing.getItem(), LetterType.NORMAL)) {
					expireRetry.put(listing.getId(), now + EXPIRE_RETRY_MILLIS); // caixa cheia: continua à venda e tenta de novo em 1 h
					continue;
				}
				expireRetry.remove(listing.getId());
				listings.remove(listing.getId());
				listing.setItem(null);
				listing.setState(State.EXPIRED);
				if (!GlobalTradeDAO.update(listing))
					log.error("[GLOBAL_TRADE] {} devolvido pelo correio, mas o estado não foi gravado", listing);
			}
		}
	}

	// ------------------------------------------------------------------ personagem

	/**
	 * @return true se o personagem tem anúncio à venda ou receita a receber (STR_MSG_WORLD_VENDOR_REMOVE_CHARACTER_CANCEL)
	 */
	public boolean hasOpenListings(int playerId) {
		return count(l -> l.getSellerId() == playerId && (l.getState() == State.LISTED || l.getState() == State.SOLD)) > 0;
	}

	/** O item anunciado sai junto com o inventory do personagem apagado; o anúncio fica cancelado. */
	public void onPlayerDeleted(int playerId) {
		synchronized (this) {
			for (GlobalTradeListing listing : List.copyOf(listings.values())) {
				if (listing.getSellerId() != playerId)
					continue;
				listings.remove(listing.getId());
				if (listing.getState() == State.LISTED) {
					listing.setItem(null);
					listing.setState(State.CANCELED);
					GlobalTradeDAO.update(listing);
				}
			}
		}
	}

	// ------------------------------------------------------------------ utilidades

	private boolean isEnabled(Player player) {
		if (!GlobalTradeConfig.ENABLE) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_RESTRICTED));
			return false;
		}
		if (player.getLevel() < GlobalTradeConfig.MIN_LEVEL) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_BELOW_STANDARD));
			return false;
		}
		return true;
	}

	private boolean canTrade(Player player) {
		if (!isEnabled(player))
			return false;
		if (!player.isOnline() || !player.isSpawned() || player.isDead() || player.isTrading() || player.hasStore()) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_CANNOT_USE_NOW));
			return false;
		}
		return true;
	}

	/**
	 * Categoria do cliente (vendor_category_index) em 4 níveis: X|YY|ZZ|WW. O pedido casa por prefixo (captura: 3000000 traz 3010000 e
	 * 3020000); abaixo de 1000000 (o "2" das capturas) é a lista inteira.
	 */
	static boolean inCategory(int itemCategory, int requested) {
		if (requested < 1_000_000)
			return true;
		for (int unit : new int[] { 1_000_000, 10_000, 100 })
			if (requested % unit == 0)
				return itemCategory / unit == requested / unit;
		return itemCategory == requested;
	}

	/**
	 * Ordem do C_GLOBAL_TRADE_LIST, tirada das listas capturadas: 4 = preço total crescente, 6 = preço unitário crescente, 7 = unitário
	 * decrescente, 8 = mais antigo primeiro. 5 e 9 são o inverso de 4 e 8 por analogia.
	 */
	static Comparator<GlobalTradeListing> comparator(int sort) {
		Comparator<GlobalTradeListing> byId = Comparator.comparingLong(GlobalTradeListing::getId);
		Comparator<GlobalTradeListing> byUnitPrice = (a, b) -> compareUnitPrice(a.getPrice(), a.getCount(), b.getPrice(), b.getCount());
		return switch (sort) {
			case 4 -> Comparator.comparingLong(GlobalTradeListing::getPrice).thenComparing(byId);
			case 5 -> Comparator.comparingLong(GlobalTradeListing::getPrice).thenComparing(byId).reversed();
			case 6 -> byUnitPrice.thenComparing(byId);
			case 7 -> byUnitPrice.thenComparing(byId).reversed();
			case 9 -> byId.reversed();
			default -> byId;
		};
	}

	/** Compara price1/count1 com price2/count2 sem arredondar (79.999.999/100 fica antes de 8.000.000/10 na ordem 7 capturada). */
	static int compareUnitPrice(long price1, long count1, long price2, long count2) {
		long high1 = Math.multiplyHigh(price1, count2), high2 = Math.multiplyHigh(price2, count1);
		return high1 != high2 ? Long.compare(high1, high2) : Long.compareUnsigned(price1 * count2, price2 * count1);
	}

	static long unitPriceX100(long price, long count) {
		return price / count * 100 + price % count * 100 / count;
	}

	/**
	 * Preço médio unitário x100 (a lista capturada traz 18.456.540 para anúncios de ~700.000 por unidade): vendas dos últimos 28 dias; sem
	 * venda, os anúncios à venda.
	 */
	private long averageUnitPriceX100(int itemId, GlobalTradeCurrency currency) {
		long since = System.currentTimeMillis() - HISTORY_MILLIS;
		long[] sold = totals(l -> l.getItemId() == itemId && l.getCurrency() == currency
			&& (l.getState() == State.SOLD || l.getState() == State.COLLECTED) && l.getSoldTime() >= since);
		long[] totals = sold[1] > 0 ? sold : totals(l -> l.getItemId() == itemId && l.getCurrency() == currency && l.getState() == State.LISTED);
		return totals[1] == 0 ? 0 : unitPriceX100(totals[0], totals[1]);
	}

	private long[] totals(Predicate<GlobalTradeListing> filter) {
		long price = 0, count = 0;
		for (GlobalTradeListing listing : listings.values())
			if (filter.test(listing)) {
				price = saturatedAdd(price, listing.getPrice());
				count = saturatedAdd(count, listing.getCount());
			}
		return new long[] { price, count };
	}

	private static long saturatedAdd(long a, long b) {
		long result = a + b;
		return result < 0 ? Long.MAX_VALUE : result;
	}

	private List<GlobalTradeListing> mine(int playerId, State state, GlobalTradeCurrency currency, Comparator<GlobalTradeListing> order) {
		return listings.values().stream().filter(l -> l.getSellerId() == playerId && l.getState() == state && l.getCurrency() == currency)
			.sorted(order).toList();
	}

	private long count(Predicate<GlobalTradeListing> filter) {
		return listings.values().stream().filter(filter).count();
	}

	private static long sum(List<GlobalTradeListing> list, java.util.function.ToLongFunction<GlobalTradeListing> value) {
		long total = 0;
		for (GlobalTradeListing listing : list)
			total = saturatedAdd(total, value.applyAsLong(listing));
		return total;
	}

	private static DescriptionId nameOf(int itemId) {
		return new DescriptionId(DataManager.ITEM_DATA.getItemTemplate(itemId).getNameId() << 1 | 1);
	}

	private static class SingletonHolder {

		private static final GlobalTradeService INSTANCE = new GlobalTradeService();
	}
}
