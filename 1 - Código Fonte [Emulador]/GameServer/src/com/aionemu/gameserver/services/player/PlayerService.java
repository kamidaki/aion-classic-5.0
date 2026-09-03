package com.aionemu.gameserver.services.player;

import java.sql.Timestamp;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.commons.utils.GenericValidator;
import com.aionemu.gameserver.configs.main.CacheConfig;
import com.aionemu.gameserver.controllers.FlyController;
import com.aionemu.gameserver.controllers.PlayerController;
import com.aionemu.gameserver.controllers.effect.PlayerEffectController;
import com.aionemu.gameserver.dao.*;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.PlayerInitialData;
import com.aionemu.gameserver.dataholders.PlayerInitialData.LocationData;
import com.aionemu.gameserver.dataholders.PlayerInitialData.PlayerCreationData;
import com.aionemu.gameserver.dataholders.PlayerInitialData.PlayerCreationData.ItemType;
import com.aionemu.gameserver.model.*;
import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.*;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.items.storage.PlayerStorage;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.skill.PlayerSkillList;
import com.aionemu.gameserver.model.stats.calc.functions.PlayerStatFunctions;
import com.aionemu.gameserver.model.stats.listeners.TitleChangeListener;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.services.PunishmentService.PunishmentType;
import com.aionemu.gameserver.services.SkillLearnService;
import com.aionemu.gameserver.services.item.ItemFactory;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.legion.LegionService;
import com.aionemu.gameserver.utils.collections.cachemap.CacheMap;
import com.aionemu.gameserver.utils.collections.cachemap.CacheMapFactory;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldPosition;
import com.aionemu.gameserver.world.knownlist.KnownList;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;

public class PlayerService {
	private static final Logger log = LoggerFactory.getLogger(PlayerService.class);

	private static final CacheMap<Integer, Player> playerCache = CacheMapFactory.createSoftCacheMap("Player", "player");

	// FIX: lock por playerObjId para evitar que duas chamadas concorrentes a getPlayer()
	// para o mesmo personagem montem duas instancias de Player independentes (cache miss
	// em ambas antes que a primeira termine de carregar). Mesmo padrao de "lock por chave"
	// ja usado em PlayerEnterWorldService.pendingEnterWorld, mas aqui como lock bloqueante
	// de verdade, pois getPlayer precisa retornar um valor util para quem chamou.
	private static final ConcurrentHashMap<Integer, Object> playerLoadLocks = new ConcurrentHashMap<>();

	public static boolean isFreeName(String name) {
		return !DAOManager.getDAO(PlayerDAO.class).isNameUsed(name);
	}

	public static boolean isOldName(String name) {
		return DAOManager.getDAO(OldNamesDAO.class).isOldName(name);
	}

	public static boolean storeNewPlayer(Player player, String accountName, int accountId) {
		return DAOManager.getDAO(PlayerDAO.class).saveNewPlayer(player.getCommonData(), accountId, accountName)
				&& DAOManager.getDAO(PlayerAppearanceDAO.class).store(player)
				&& DAOManager.getDAO(PlayerSkillListDAO.class).storeSkills(player)
				&& DAOManager.getDAO(InventoryDAO.class).store(player);
	}

	public static void storePlayer(Player player) {
		if (player == null) return;
		try {
			DAOManager.getDAO(PlayerDAO.class).storePlayer(player);
			DAOManager.getDAO(PlayerSkillListDAO.class).storeSkills(player);
			DAOManager.getDAO(PlayerSettingsDAO.class).saveSettings(player);
			DAOManager.getDAO(PlayerQuestListDAO.class).store(player);
			DAOManager.getDAO(AbyssRankDAO.class).storeAbyssRank(player);
			//DAOManager.getDAO(PlayerPunishmentsDAO.class).storePlayerPunishments(player, PunishmentType.PRISON);
			//DAOManager.getDAO(PlayerPunishmentsDAO.class).storePlayerPunishments(player, PunishmentType.GATHER);
			DAOManager.getDAO(InventoryDAO.class).store(player);
			DAOManager.getDAO(ItemStoneListDAO.class).save(player);
			DAOManager.getDAO(MailDAO.class).storeMailbox(player);
			DAOManager.getDAO(PortalCooldownsDAO.class).storePortalCooldowns(player);
			DAOManager.getDAO(CraftCooldownsDAO.class).storeCraftCooldowns(player);
			DAOManager.getDAO(PlayerNpcFactionsDAO.class).storeNpcFactions(player);
			DAOManager.getDAO(EventItemsDAO.class).storeItems(player);
		} catch (Throwable ex) {
			// FIX: era catch (Exception ex). Este metodo roda periodicamente via GeneralUpdateTask
			// agendada no ThreadPoolManager; um Error nao capturado aqui pode encerrar silenciosamente
			// as proximas execucoes agendadas para este player (deixa de salvar sem log nenhum).
			// Ampliado para Throwable, consistente com o catch do enter world.
            log.error("Exception during storing player {}", player.getName(), ex);
		}
	}

	public static Player getPlayer(int playerObjId, Account account) {
		if (account == null) return null;
		if (CacheConfig.CACHE_PLAYERS) {
			// Fast path sem lock: cobre o caso comum (player ja em cache, online e valido de
			// verdade), evitando pagar o custo de sincronizacao em toda chamada.
			Player cachedPlayer = playerCache.get(playerObjId);
			if (cachedPlayer != null && isCachedPlayerValid(cachedPlayer, playerObjId)) {
				return cachedPlayer;
			}
		}

		Object lock = playerLoadLocks.computeIfAbsent(playerObjId, id -> new Object());
		synchronized (lock) {
			try {
				if (CacheConfig.CACHE_PLAYERS) {
					// Double-checked locking: outra thread pode ter terminado de carregar (ou
					// invalidado) o cache enquanto esperavamos o lock.
					Player cachedPlayer = playerCache.get(playerObjId);
					if (cachedPlayer != null) {
						if (isCachedPlayerValid(cachedPlayer, playerObjId)) {
							return cachedPlayer;
						}
						playerCache.remove(playerObjId);
					}
				}
				PlayerAccountData playerAccountData = account.getPlayerAccountData(playerObjId);
				if (playerAccountData == null) {
					return null;
				}
				PlayerCommonData pcd = playerAccountData.getPlayerCommonData();
				if (pcd == null) {
					return null;
				}
				PlayerAppearance appearance = playerAccountData.getAppereance();
				Player player = new Player(new PlayerController(), pcd, appearance, account);
				LegionMember legionMember = LegionService.getInstance().getLegionMember(player.getObjectId());
				if (legionMember != null) {
					player.setLegionMember(legionMember);
				}
				MacroList macroses = DAOManager.getDAO(PlayerMacrossesDAO.class).restoreMacrosses(playerObjId);
				player.setMacroList(macroses);
				player.setSkillList(DAOManager.getDAO(PlayerSkillListDAO.class).loadSkillList(playerObjId));
				player.setKnownlist(new KnownList(player));
				player.setFriendList(DAOManager.getDAO(FriendListDAO.class).load(player));
				player.setBlockList(DAOManager.getDAO(BlockListDAO.class).load(player));
				player.setTitleList(DAOManager.getDAO(PlayerTitleListDAO.class).loadTitleList(playerObjId));
				player.setPlayerSettings(DAOManager.getDAO(PlayerSettingsDAO.class).loadSettings(playerObjId));
				DAOManager.getDAO(AbyssRankDAO.class).loadAbyssRank(player);
				DAOManager.getDAO(PlayerNpcFactionsDAO.class).loadNpcFactions(player);
				DAOManager.getDAO(MotionDAO.class).loadMotionList(player);
				player.setVars(DAOManager.getDAO(PlayerVarsDAO.class).load(player.getObjectId()));
				Equipment equipment = DAOManager.getDAO(InventoryDAO.class).loadEquipment(player);
				ItemService.loadItemStones(equipment.getEquippedItemsWithoutStigma());
				equipment.setOwner(player);
				player.setEquipment(equipment);
				player.setEffectController(new PlayerEffectController(player));
				player.setFlyController(new FlyController(player));
				PlayerStatFunctions.addPredefinedStatFunctions(player);
				player.setQuestStateList(DAOManager.getDAO(PlayerQuestListDAO.class).load(player));
				player.setRecipeList(DAOManager.getDAO(PlayerRecipesDAO.class).load(player.getObjectId()));
				Storage accWarehouse = account.getAccountWarehouse();
				if (accWarehouse != null) {
					accWarehouse.setOwner(player);
					player.setStorage(accWarehouse, StorageType.ACCOUNT_WAREHOUSE);
				}
				Storage inventory = DAOManager.getDAO(InventoryDAO.class).loadStorage(playerObjId, StorageType.CUBE);
				ItemService.loadItemStones(inventory.getItems());
				player.setStorage(inventory, StorageType.CUBE);
				for (int petBagId = StorageType.PET_BAG_MIN; petBagId <= StorageType.PET_BAG_MAX; petBagId++) {
					Storage petBag = DAOManager.getDAO(InventoryDAO.class).loadStorage(playerObjId,
							StorageType.getStorageTypeById(petBagId));
					ItemService.loadItemStones(petBag.getItems());
					player.setStorage(petBag, StorageType.getStorageTypeById(petBagId));
				}
				Storage warehouse = DAOManager.getDAO(InventoryDAO.class).loadStorage(playerObjId,
						StorageType.REGULAR_WAREHOUSE);
				ItemService.loadItemStones(warehouse.getItems());
				player.setStorage(warehouse, StorageType.REGULAR_WAREHOUSE);
				player.getEquipment().onLoadApplyEquipmentStats();
				//DAOManager.getDAO(PlayerPunishmentsDAO.class).loadPlayerPunishments(player, PunishmentType.PRISON);
				//DAOManager.getDAO(PlayerPunishmentsDAO.class).loadPlayerPunishments(player, PunishmentType.GATHER);
				player.getController().updatePassiveStats();
				DAOManager.getDAO(PlayerEffectsDAO.class).loadPlayerEffects(player);
				DAOManager.getDAO(PlayerCooldownsDAO.class).loadPlayerCooldowns(player);
				DAOManager.getDAO(ItemCooldownsDAO.class).loadItemCooldowns(player);
				DAOManager.getDAO(PortalCooldownsDAO.class).loadPortalCooldowns(player);
				DAOManager.getDAO(PlayerBindPointDAO.class).loadBindPoint(player);
				DAOManager.getDAO(CraftCooldownsDAO.class).loadCraftCooldowns(player);
				if (player.getCommonData().getTitleId() > 0) {
					TitleChangeListener.onTitleChange(player.getGameStats(), player.getCommonData().getTitleId(), true);
				}
				DAOManager.getDAO(PlayerLifeStatsDAO.class).loadPlayerLifeStat(player);
				DAOManager.getDAO(PlayerEmotionListDAO.class).loadEmotions(player);
				DAOManager.getDAO(PlayerEquipmentSettingDAO.class).loadEquipmentSetting(player);
				if (CacheConfig.CACHE_PLAYERS) {
					playerCache.put(playerObjId, player);
				}
				return player;
			} finally {
				// Remove o lock somente se ainda for o mesmo objeto que colocamos (evita remover
				// o lock de uma chamada mais nova que tenha entrado depois de nos).
				playerLoadLocks.remove(playerObjId, lock);
			}
		}
	}

	/**
	 * FIX: valida que um player em cache marcado como "online" esta de fato presente no
	 * World antes de reaproveita-lo. Sem essa checagem, uma flag "online" que ficou stale
	 * (ex: desconexao sem cleanup completo, crash no meio do enter world) faria este metodo
	 * devolver um objeto Player incompleto/desatualizado para um novo login ou lookup,
	 * pulando toda a recarga de estado feita abaixo (skills, storages, efeitos, cooldowns...).
	 */
	private static boolean isCachedPlayerValid(Player cachedPlayer, int playerObjId) {
		return cachedPlayer.isOnline() && World.getInstance().findPlayer(playerObjId) != null;
	}

	public static Player newPlayer(PlayerCommonData playerCommonData, PlayerAppearance playerAppearance,
								   Account account) {
		PlayerInitialData playerInitialData = DataManager.PLAYER_INITIAL_DATA;
		LocationData ld = null;
		if (playerCommonData.getPlayerClass() == PlayerClass.REVENANT) {
			try {
				ld = playerInitialData.getTelosSpawnLocation(playerCommonData.getRace());
			} catch (Exception e) {
				log.warn("Telos spawn location not available for race {}", playerCommonData.getRace(), e);
			}
		}
		if (ld == null) {
			try {
				ld = playerInitialData.getSpawnLocation(playerCommonData.getRace());
			} catch (Exception e) {
				log.warn("Standard spawn location not available for race {}", playerCommonData.getRace(), e);
			}
		}
		// FIX: removido o fallback com coordenadas hardcoded (mapId 210010000 / 220010000 e
		// demais valores fixos). A posicao de spawn agora SEMPRE vem do PLAYER_INITIAL_DATA.
		// Se nao houver spawn location cadastrada para a raca/classe (nenhuma das duas
		// tentativas acima retornou algo), isso e um erro de dados de configuracao e deve
		// falhar de forma visivel, em vez de nascer o personagem numa posicao inventada.
		if (ld == null) {
			throw new IllegalStateException("Nenhuma spawn location cadastrada no PLAYER_INITIAL_DATA para raca="
					+ playerCommonData.getRace() + ", classe=" + playerCommonData.getPlayerClass()
					+ ". Verifique player_initial_data.xml.");
		}
		int mapId = ld.getMapId();
		float x = ld.getX();
		float y = ld.getY();
		float z = ld.getZ();
		byte heading = ld.getHeading();

		WorldPosition position = World.getInstance().createPosition(mapId, x, y, z, heading, 0);
		playerCommonData.setPosition(position);
		Player newPlayer = new Player(new PlayerController(), playerCommonData, playerAppearance, account);
		newPlayer.setPlayerSettings(new PlayerSettings());
		newPlayer.setSkillList(new PlayerSkillList());
		SkillLearnService.addNewSkills(newPlayer);
		PlayerCreationData playerCreationData = playerInitialData
				.getPlayerCreationData(playerCommonData.getPlayerClass());
		Storage playerInventory = new PlayerStorage(StorageType.CUBE);
		Storage regularWarehouse = new PlayerStorage(StorageType.REGULAR_WAREHOUSE);
		Storage accountWarehouse = new PlayerStorage(StorageType.ACCOUNT_WAREHOUSE);
		Equipment equipment = new Equipment(newPlayer);
		if (playerCreationData != null) {
			List<ItemType> items = playerCreationData.getItems();
			for (ItemType itemType : items) {
				if (itemType.getRace() != null && itemType.getRace() != Race.PC_ALL && itemType.getRace() != newPlayer.getRace())
					continue;

				if (itemType.getTemplate() == null)
					continue;

				int itemId = itemType.getTemplate().getTemplateId();
				Item item = ItemFactory.newItem(itemId, itemType.getCount());
				if (item == null) {
					continue;
				}
				ItemTemplate itemTemplate = item.getItemTemplate();
				if ((itemTemplate.isArmor() || itemTemplate.isWeapon())
						&& itemTemplate.getItemSlot() != 0
						&& !equipment.isSlotEquipped(itemTemplate.getItemSlot())) {
					ItemSlot freeSlot = equipment.getFirstFreeSlot(itemTemplate.getItemSlot());
					if (freeSlot != null) {
						item.setEquipped(true);
						item.setEquipmentSlot(freeSlot.getSlotIdMask());
						equipment.onLoadHandler(item);
					} else {
						playerInventory.onLoadHandler(item);
					}
				} else {
					playerInventory.onLoadHandler(item);
				}
			}
		}
		newPlayer.setStorage(playerInventory, StorageType.CUBE);
		newPlayer.setStorage(regularWarehouse, StorageType.REGULAR_WAREHOUSE);
		newPlayer.setStorage(accountWarehouse, StorageType.ACCOUNT_WAREHOUSE);
		newPlayer.setEquipment(equipment);
		newPlayer.setMailbox(new Mailbox(newPlayer));
		for (int petBagId = StorageType.PET_BAG_MIN; petBagId <= StorageType.PET_BAG_MAX; petBagId++) {
			Storage petBag = new PlayerStorage(StorageType.getStorageTypeById(petBagId));
			newPlayer.setStorage(petBag, StorageType.getStorageTypeById(petBagId));
		}
		playerInventory.setPersistentState(PersistentState.UPDATE_REQUIRED);
		equipment.setPersistentState(PersistentState.UPDATE_REQUIRED);
		return newPlayer;
	}

	public static boolean cancelPlayerDeletion(PlayerAccountData accData) {
		if (accData.getDeletionDate() == null) {
			return true;
		}
		if (accData.getDeletionDate().getTime() > System.currentTimeMillis()) {
			accData.setDeletionDate(null);
			storeDeletionTime(accData);
			return true;
		}
		return false;
	}

	public static void deletePlayer(PlayerAccountData accData) {
		if (accData.getDeletionDate() != null) {
			return;
		}
		accData.setDeletionDate(new Timestamp(System.currentTimeMillis() + 5 * 60 * 1000));
		storeDeletionTime(accData);
	}

	public static void deletePlayerFromDB(int playerId) {
		DAOManager.getDAO(InventoryDAO.class).deletePlayerItems(playerId);
		DAOManager.getDAO(PlayerDAO.class).deletePlayer(playerId);
		playerCache.remove(playerId);
	}

	public static int deleteAccountsCharsFromDB(int accountId) {
		List<Integer> charIds = DAOManager.getDAO(PlayerDAO.class).getPlayerOidsOnAccount(accountId);
		if (charIds == null || charIds.isEmpty()) {
			return 0;
		}
		for (int playerId : charIds) {
			deletePlayerFromDB(playerId);
		}
		return charIds.size();
	}

	private static void storeDeletionTime(PlayerAccountData accData) {
		DAOManager.getDAO(PlayerDAO.class).updateDeletionTime(accData.getPlayerCommonData().getPlayerObjId(),
				accData.getDeletionDate());
	}

	public static void storeCreationTime(int objectId, Timestamp creationDate) {
		DAOManager.getDAO(PlayerDAO.class).storeCreationTime(objectId, creationDate);
	}

	public static void addMacro(Player player, int macroOrder, String macroXML) {
		if (player.getMacroList().addMacro(macroOrder, macroXML)) {
			DAOManager.getDAO(PlayerMacrossesDAO.class).addMacro(player.getObjectId(), macroOrder, macroXML);
		} else {
			DAOManager.getDAO(PlayerMacrossesDAO.class).updateMacro(player.getObjectId(), macroOrder, macroXML);
		}
	}

	public static void removeMacro(Player player, int macroOrder) {
		if (player.getMacroList().removeMacro(macroOrder)) {
			DAOManager.getDAO(PlayerMacrossesDAO.class).deleteMacro(player.getObjectId(), macroOrder);
		}
	}

	public static Player getCachedPlayer(int playerObjectId) {
		return playerCache.get(playerObjectId);
	}

	public static void removeCachedPlayer(int playerObjectId) {
		playerCache.remove(playerObjectId);
	}

	public static String getPlayerName(Integer objectId) {
		return getPlayerNames(Collections.singleton(objectId)).get(objectId);
	}

	public static Map<Integer, String> getPlayerNames(Collection<Integer> playerObjIds) {
		if (GenericValidator.isBlankOrNull(playerObjIds)) {
			return Collections.emptyMap();
		}
		final Map<Integer, String> result = Maps.newHashMap();
		final Set<Integer> playerObjIdsCopy = Sets.newHashSet(playerObjIds);
		for (Iterator<Integer> it = playerObjIdsCopy.iterator(); it.hasNext(); ) {
			int id = it.next();
			Player onlinePlayer = World.getInstance().findPlayer(id);
			if (onlinePlayer != null) {
				result.put(id, onlinePlayer.getName());
				it.remove();
			}
		}
		if (!playerObjIdsCopy.isEmpty()) {
			result.putAll(DAOManager.getDAO(PlayerDAO.class).getPlayerNames(playerObjIdsCopy));
		}
		return result;
	}
}