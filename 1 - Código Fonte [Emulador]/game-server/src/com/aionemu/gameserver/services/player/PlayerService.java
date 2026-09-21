package com.aionemu.gameserver.services.player;

import java.sql.Timestamp;
import java.util.List;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.configs.main.EventsConfig;
import com.aionemu.gameserver.configs.main.MembershipConfig;
import com.aionemu.gameserver.configs.main.NameConfig;
import java.util.concurrent.CompletableFuture;
import com.aionemu.gameserver.controllers.FlyController;
import com.aionemu.gameserver.controllers.effect.PlayerEffectController;
import com.aionemu.gameserver.dao.*;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.PlayerInitialData;
import com.aionemu.gameserver.dataholders.PlayerInitialData.LocationData;
import com.aionemu.gameserver.dataholders.PlayerInitialData.PlayerCreationData;
import com.aionemu.gameserver.dataholders.PlayerInitialData.PlayerCreationData.ItemType;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Mailbox;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.house.House;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.skill.PlayerSkillList;
import com.aionemu.gameserver.model.stats.calc.functions.PlayerStatFunctions;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.actions.EmotionLearnAction;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DELETE_CHARACTER;
import com.aionemu.gameserver.services.AccountService;
import com.aionemu.gameserver.services.BrokerService;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;
import com.aionemu.gameserver.services.HousingService;
import com.aionemu.gameserver.services.LegionService;
import com.aionemu.gameserver.services.PunishmentService.PunishmentType;
import com.aionemu.gameserver.services.SkillLearnService;
import com.aionemu.gameserver.services.item.ItemFactory;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.knownlist.KnownList;

/**
 * @author Lost Academy Team & Durak
 */
public class PlayerService {

	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(PlayerService.class);

	/**
	 * @return True if the character name is taken (currently used by another character or the character with this name was recently renamed).
	 */
	public static boolean isNameUsedOrReserved(String oldName, String newName) {
		return isNameUsedOrReserved(oldName, newName, NameConfig.RESERVE_OLD_NAME_DAYS);
	}

	public static boolean isNameUsedOrReserved(String oldName, String newName, int nameReservationDurationDays) {
		return PlayerDAO.isNameUsed(newName) || OldNamesDAO.isNameReserved(oldName, newName, nameReservationDurationDays);
	}

	/**
	 * Stores newly created player
	 *
	 * @param player
	 *          player to store
	 * @return true if character was successful saved.
	 */
	public static boolean storeNewPlayer(Player player, String accountName, int accountId) {
		if (!PlayerDAO.saveNewPlayer(player, accountId, accountName)) {
			return false;
		}
		var fAppearance = CompletableFuture.supplyAsync(() -> PlayerAppearanceDAO.store(player));
		var fSkills = CompletableFuture.supplyAsync(() -> PlayerSkillListDAO.storeSkills(player));
		var fInventory = CompletableFuture.supplyAsync(() -> InventoryDAO.store(player));

		try {
			boolean success = fAppearance.get() && fSkills.get() && fInventory.get();
			if (!success) {
				deletePlayerFromDB(player.getObjectId());
				return false;
			}
			return true;
		} catch (Exception e) {
			log.error("Error storing new player subsystems for " + player.getName(), e);
			deletePlayerFromDB(player.getObjectId());
			return false;
		}
	}

	/**
	 * Stores player data into db
	 *
	 * @param player
	 */
	public static void storePlayer(Player player) {
		PlayerDAO.storePlayer(player);
		PlayerSkillListDAO.storeSkills(player);
		PlayerSettingsDAO.saveSettings(player);
		PlayerQuestListDAO.store(player);
		AbyssRankDAO.storeAbyssRank(player);
		PlayerPunishmentsDAO.storePlayerPunishment(player, PunishmentType.PRISON);
		PlayerPunishmentsDAO.storePlayerPunishment(player, PunishmentType.GATHER);
		InventoryDAO.store(player);
		for (House house : player.getHouses())
			house.save();
		ItemStoneListDAO.save(player);
		MailDAO.storeMailbox(player);
		PortalCooldownsDAO.storePortalCooldowns(player);
		CraftCooldownsDAO.storeCraftCooldowns(player);
		HouseObjectCooldownsDAO.storeHouseObjectCooldowns(player);
		PlayerNpcFactionsDAO.storeNpcFactions(player);
		AccountPassportsDAO.storePassport(player.getAccount());
		player.clearDirty(Player.DirtyFlag.ABYSS_RANK);
		player.clearDirty(Player.DirtyFlag.SKILLS);
		player.clearDirty(Player.DirtyFlag.QUESTS);
		player.clearDirty(Player.DirtyFlag.INVENTORY);
	}

	public static Player getPlayer(int playerObjId, Account account) {
		// Player common data and appearance should be already loaded in account
		PlayerAccountData playerAccountData = account.getPlayerAccountData(playerObjId);
		PlayerCommonData pcd = playerAccountData.getPlayerCommonData();
		Player player = new Player(playerAccountData, account);
		int oldOwnerId = pcd.getWorldOwnerId();
		player.setPosition(World.getInstance().createPosition(pcd.getMapId(), pcd.getX(), pcd.getY(), pcd.getZ(), pcd.getHeading(), 0));
		pcd.setWorldOwnerId(oldOwnerId);
		LegionMember legionMember = LegionService.getInstance().getLegionMember(pcd);
		if (legionMember != null) {
			player.setLegionMember(legionMember);
		}

		// Parallelize independent database loads to eliminate sequential network latency
		var macrosFuture = CompletableFuture.supplyAsync(() -> PlayerMacrosDAO.loadMacros(playerObjId));
		var skillFuture = CompletableFuture.supplyAsync(() -> PlayerSkillListDAO.loadSkillList(playerObjId));
		var friendFuture = CompletableFuture.supplyAsync(() -> FriendListDAO.load(player));
		var blockFuture = CompletableFuture.supplyAsync(() -> BlockListDAO.load(playerObjId));
		var titleFuture = CompletableFuture.supplyAsync(() -> PlayerTitleListDAO.loadTitleList(playerObjId));
		var settingsFuture = CompletableFuture.supplyAsync(() -> PlayerSettingsDAO.loadSettings(playerObjId));
		var questFuture = CompletableFuture.supplyAsync(() -> PlayerQuestListDAO.load(playerObjId));
		var recipeFuture = CompletableFuture.supplyAsync(() -> PlayerRecipesDAO.load(player.getObjectId()));
		var abyssFuture = CompletableFuture.runAsync(() -> AbyssRankDAO.loadAbyssRank(player));
		var factionsFuture = CompletableFuture.runAsync(() -> PlayerNpcFactionsDAO.loadNpcFactions(player));
		var motionFuture = CompletableFuture.runAsync(() -> MotionDAO.loadMotionList(player));
		var passportFuture = CompletableFuture.runAsync(() -> AccountPassportsDAO.loadPassport(player.getAccount()));

		player.setKnownlist(new KnownList(player));
		player.setEffectController(new PlayerEffectController(player));
		player.setFlyController(new FlyController(player));
		PlayerStatFunctions.addPredefinedStatFunctions(player);

		player.setSkillList(skillFuture.join());
		account.getAccountWarehouse().setOwner(player);
		InventoryDAO.loadStorage(playerObjId, player.getInventory());
		ItemStoneListDAO.load(player.getInventory().getItems());
		ItemStoneListDAO.load(player.getEquipment().getEquippedItemsWithoutStigma());

		InventoryDAO.loadStorage(playerObjId, player.getWarehouse());
		ItemStoneListDAO.load(player.getWarehouse().getItems());

		for (Storage petBag : player.getPetBags()) {
			InventoryDAO.loadStorage(playerObjId, petBag);
			ItemStoneListDAO.load(petBag.getItems());
		}
		for (Storage cabinet : player.getCabinets()) {
			InventoryDAO.loadStorage(playerObjId, cabinet);
			ItemStoneListDAO.load(cabinet.getItems());
		}

		player.setMacros(macrosFuture.join());
		player.setFriendList(friendFuture.join());
		player.setBlockList(blockFuture.join());
		player.setTitleList(titleFuture.join());
		player.setPlayerSettings(settingsFuture.join());
		player.setQuestStateList(questFuture.join());
		player.setRecipeList(recipeFuture.join());
		abyssFuture.join();
		factionsFuture.join();
		motionFuture.join();
		passportFuture.join();

		// Apply equipment stats (items and manastones were loaded in account)
		player.getEquipment().onLoadApplyEquipmentStats();

		var punishmentsFuture = CompletableFuture.runAsync(() -> PlayerPunishmentsDAO.loadPlayerPunishments(player));
		var effectsFuture = CompletableFuture.runAsync(() -> PlayerEffectsDAO.loadPlayerEffects(player));
		var playerCooldownsFuture = CompletableFuture.runAsync(() -> PlayerCooldownsDAO.loadPlayerCooldowns(player));
		var itemCooldownsFuture = CompletableFuture.runAsync(() -> ItemCooldownsDAO.loadItemCooldowns(player));
		var portalCooldownsFuture = CompletableFuture.runAsync(() -> PortalCooldownsDAO.loadPortalCooldowns(player));
		var houseCooldownsFuture = CompletableFuture.runAsync(() -> HouseObjectCooldownsDAO.loadHouseObjectCooldowns(player));
		var bindPointFuture = CompletableFuture.runAsync(() -> PlayerBindPointDAO.loadBindPoint(player));
		var craftCooldownsFuture = CompletableFuture.runAsync(() -> CraftCooldownsDAO.loadCraftCooldowns(player));
		var lifeStatsFuture = CompletableFuture.runAsync(() -> PlayerLifeStatsDAO.loadPlayerLifeStat(player));
		var emotionsFuture = CompletableFuture.runAsync(() -> PlayerEmotionListDAO.loadEmotions(player));

		punishmentsFuture.join();
		effectsFuture.join();
		playerCooldownsFuture.join();
		itemCooldownsFuture.join();
		portalCooldownsFuture.join();
		houseCooldownsFuture.join();
		bindPointFuture.join();
		craftCooldownsFuture.join();
		lifeStatsFuture.join();
		emotionsFuture.join();
		if (player.hasPermission(MembershipConfig.EMOTIONS_ALL)) {
			for (int emotionId : EmotionLearnAction.getLearnableEmotionIds())
				player.getEmotions().add(emotionId, 0, false);
		}

		PlayerEquipmentSettingDAO.loadEquipmentSetting(player);
		MorosService.onLoad(player);
		StorybookService.onLoad(player);
		PlayerWardrobeService.getInstance().onLoad(player);

		return player;
	}

	/**
	 * This method is used for creating new players
	 *
	 * @param playerAccountData
	 * @param account
	 * @return Player
	 */
	public static Player newPlayer(PlayerAccountData playerAccountData, Account account) {
		PlayerCommonData playerCommonData = playerAccountData.getPlayerCommonData();
		PlayerInitialData playerInitialData = DataManager.PLAYER_INITIAL_DATA;
		LocationData ld = (playerCommonData.getPlayerClass() == PlayerClass.REVENANT)
			? playerInitialData.getTelosSpawnLocation(playerCommonData.getRace())
			: playerInitialData.getSpawnLocation(playerCommonData.getRace());

		playerCommonData.setMapId(ld.getMapId());
		playerCommonData.setX(ld.getX());
		playerCommonData.setY(ld.getY());
		playerCommonData.setZ(ld.getZ());
		playerCommonData.setHeading(ld.getHeading());

		Player newPlayer = new Player(playerAccountData, account);

		// Starting skills
		newPlayer.setSkillList(new PlayerSkillList());
		SkillLearnService.learnNewSkills(newPlayer, 1, newPlayer.getLevel());

		// Starting items
		PlayerCreationData playerCreationData = playerInitialData.getPlayerCreationData(playerCommonData.getPlayerClass());
		if (playerCreationData != null) { // player transfer
			List<ItemType> items = playerCreationData.getItems();
			for (ItemType itemType : items) {
				int itemId = itemType.getTemplate().getTemplateId();
				Item item = ItemFactory.newItem(itemId, itemType.getCount());
				if (item == null) {
					continue;
				}

				// When creating new player - all equipment that has slot values will be equipped
				// Make sure you will not put into xml file more items than possible to equip.
				ItemTemplate itemTemplate = item.getItemTemplate();

				if (itemTemplate.isArmor() || itemTemplate.isWeapon()) {
					if (itemTemplate.isTwoHandWeapon()) {
						if (!newPlayer.getEquipment().isSlotEquipped(ItemSlot.MAIN_HAND.getSlotIdMask())
							&& !newPlayer.getEquipment().isSlotEquipped(ItemSlot.SUB_HAND.getSlotIdMask())) {
							item.setEquipped(true);
							item.setEquipmentSlot(ItemSlot.MAIN_OR_SUB.getSlotIdMask());
						}
					} else {
						for (ItemSlot slot : ItemSlot.getSlotsFor(itemTemplate.getItemSlot())) {
							if (!newPlayer.getEquipment().isSlotEquipped(slot.getSlotIdMask())) {
								item.setEquipped(true);
								item.setEquipmentSlot(slot.getSlotIdMask());
								break;
							}
						}
					}
				}
				if (item.isEquipped()) {
					newPlayer.getEquipment().onLoadHandler(item);
				} else {
					newPlayer.getInventory().onLoadHandler(item);
				}
			}
		}
		newPlayer.setMailbox(new Mailbox(newPlayer));

		// Mark inventory and equipment as UPDATE_REQUIRED to be saved during character creation
		newPlayer.getInventory().setPersistentState(PersistentState.UPDATE_REQUIRED);
		newPlayer.getEquipment().setPersistentState(PersistentState.UPDATE_REQUIRED);
		return newPlayer;
	}

	public static PlayerCommonData getOrLoadPlayerCommonData(int playerObjId) {
		Player player = World.getInstance().getPlayer(playerObjId);
		if (player == null)
			return PlayerDAO.loadPlayerCommonData(playerObjId);
		return player.getCommonData();
	}

	public static PlayerCommonData getOrLoadPlayerCommonData(String name) {
		Player player = World.getInstance().getPlayer(name);
		if (player == null)
			return PlayerDAO.loadPlayerCommonDataByName(name);
		return player.getCommonData();
	}

	/**
	 * Cancel Player deletion process if its possible.
	 *
	 * @param accData
	 *          PlayerAccountData
	 * @return True if deletion was successful canceled.
	 */
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

	/**
	 * Starts player deletion process if its possible. If deletion is possible character should be deleted after 5 minutes.
	 *
	 * @param accData
	 *          PlayerAccountData
	 */
	public static boolean deletePlayer(PlayerAccountData accData) {
		if (accData.getDeletionDate() != null) {
			if (accData.getDeletionDate().getTime() <= System.currentTimeMillis() || CustomConfig.CHARACTER_DELETION_TIME_MINUTES == 0) {
				deletePlayerFromDB(accData.getPlayerCommonData().getPlayerObjId());
				return true;
			}
			return false;
		}

		if (CustomConfig.CHARACTER_DELETION_TIME_MINUTES == 0
				|| accData.getPlayerCommonData().getLevel() < CustomConfig.CHARACTER_DELETION_MIN_LEVEL) {
			deletePlayerFromDB(accData.getPlayerCommonData().getPlayerObjId());
			return true;
		}

		accData.setDeletionDate(new Timestamp(System.currentTimeMillis() + CustomConfig.CHARACTER_DELETION_TIME_MINUTES * 60 * 1000L));
		storeDeletionTime(accData);
		return false;
	}

	/**
	 * Schedules character deletion in real time while player is in character selection (AUTHED state).
	 * Automatically deletes from DB and notifies client via SM_DELETE_CHARACTER(chaOid, 0) upon expiry.
	 */
	public static void scheduleCharacterDeletion(AionConnection conn, int chaOid, long deletionTimeMs) {
		long delayMs = Math.max(0, deletionTimeMs - System.currentTimeMillis());
		ThreadPoolManager.getInstance().schedule(() -> {
			try {
				if (conn == null || conn.getState() != State.AUTHED) {
					return;
				}
				Account acc = conn.getAccount();
				if (acc == null) {
					return;
				}
				PlayerAccountData pad = acc.getPlayerAccountData(chaOid);
				if (pad != null && pad.getDeletionDate() != null && pad.getDeletionDate().getTime() <= System.currentTimeMillis()) {
					deletePlayerFromDB(chaOid);
					acc.removePlayerAccountData(chaOid);
					AccountService.invalidateCache(acc.getId());
					conn.sendPacket(new SM_DELETE_CHARACTER(chaOid, 0));
					log.info("CM_DELETE_CHARACTER: Tempo expirado. O personagem {} foi deletado automaticamente.", chaOid);
				}
			} catch (Exception e) {
				log.error("Erro ao processar delecao automatica de personagem " + chaOid, e);
			}
		}, delayMs);
	}

	/**
	 * Completely removes player from database
	 *
	 * @param playerId
	 *          id of player to delete from db
	 */
	public static void deletePlayerFromDB(int playerId) {
		deletePlayerFromDB(playerId, true);
	}

	public static void deletePlayerFromDB(int playerId, boolean notifyServices) {
		InventoryDAO.deletePlayerOrLegionItems(playerId);
		PlayerDAO.deletePlayer(playerId);
		if (notifyServices) {
			HousingService.getInstance().onPlayerDeleted(playerId);
			BrokerService.getInstance().onPlayerDeleted(playerId);
			GlobalTradeService.getInstance().onPlayerDeleted(playerId);
		}
	}

	/**
	 * Updates deletion time in database
	 *
	 * @param accData
	 *          PlayerAccountData
	 */
	private static void storeDeletionTime(PlayerAccountData accData) {
		PlayerDAO.updateDeletionTime(accData.getPlayerCommonData().getPlayerObjId(), accData.getDeletionDate());
	}

	/**
	 * @param objectId
	 * @param creationDate
	 */
	public static void storeCreationTime(int objectId, Timestamp creationDate) {
		PlayerDAO.storeCreationTime(objectId, creationDate);
	}

	/**
	 * Add macro for player
	 *
	 * @param player
	 *          Player
	 * @param macroOrder
	 *          Macro order
	 * @param macroXML
	 *          Macro XML
	 */
	public static void addMacro(Player player, int macroOrder, String macroXML) {
		if (player.getMacros().add(macroOrder, macroXML)) {
			PlayerMacrosDAO.addMacro(player.getObjectId(), macroOrder, macroXML);
		} else {
			PlayerMacrosDAO.updateMacro(player.getObjectId(), macroOrder, macroXML);
		}
	}

	/**
	 * Remove macro with specified index from specified player
	 *
	 * @param player
	 *          Player
	 * @param macroOrder
	 *          Macro order index
	 */
	public static void removeMacro(Player player, int macroOrder) {
		if (player.getMacros().remove(macroOrder)) {
			PlayerMacrosDAO.deleteMacro(player.getObjectId(), macroOrder);
		}
	}

	public static String getPlayerName(int objectId) {
		Player player = World.getInstance().getPlayer(objectId);
		if (player != null)
			return player.getName();
		return PlayerDAO.getPlayerNameByObjId(objectId);
	}
}
