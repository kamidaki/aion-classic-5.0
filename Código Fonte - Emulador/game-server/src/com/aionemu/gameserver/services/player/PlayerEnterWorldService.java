package com.aionemu.gameserver.services.player;

import static com.aionemu.gameserver.configs.main.SecurityConfig.MultiClientingRestrictionMode.SAME_FACTION;

import java.sql.Timestamp;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.lostacademy.nav.NavData;
import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.configs.main.GSConfig;
import com.aionemu.gameserver.configs.main.PeriodicSaveConfig;
import com.aionemu.gameserver.configs.main.SecurityConfig;
import com.aionemu.gameserver.dao.*;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.PlayerInitialData;
import com.aionemu.gameserver.model.Expirable;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.CharacterPasskey.ConnectType;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.BindPointPosition;
import com.aionemu.gameserver.model.gameobjects.player.FriendList.Status;
import com.aionemu.gameserver.model.gameobjects.player.Macros;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.gameobjects.player.emotion.Emotion;
import com.aionemu.gameserver.model.gameobjects.player.motion.Motion;
import com.aionemu.gameserver.model.gameobjects.player.title.Title;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.house.House;
import com.aionemu.gameserver.model.items.storage.IStorage;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.siege.FortressLocation;
import com.aionemu.gameserver.model.team.alliance.PlayerAllianceService;
import com.aionemu.gameserver.model.team.group.PlayerGroupService;
import com.aionemu.gameserver.model.templates.housing.HouseAddress;
import com.aionemu.gameserver.model.templates.housing.HouseType;
import com.aionemu.gameserver.model.vortex.VortexLocation;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ENTER_WORLD_CHECK.Msg;
import com.aionemu.gameserver.services.*;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.services.LegionService;
import com.aionemu.gameserver.services.SkillLearnService;
import com.aionemu.gameserver.services.mail.MailService;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.services.toypet.PetService;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.taskmanager.tasks.ExpireTimerTask;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.utils.collections.DynamicServerPacketBodySplitList;
import com.aionemu.gameserver.utils.collections.SplitList;
import com.aionemu.gameserver.world.World;

/**
 * PlayerEnterWorldService - Classic 5.0 (EU).
 * Sequencia estrita de login e entrada no mundo alinhada ao PCAP oficial e comprovada no 7 - BACKUP EMULADOR.
 */
public final class PlayerEnterWorldService {

	private static final Logger log = LoggerFactory.getLogger("GAMECONNECTION_LOG");
	private static final Set<Integer> enteringWorld = ConcurrentHashMap.newKeySet();

	public static void startEnterWorld(final int objectId, final AionConnection client) {
		log.info("[ENTER_WORLD] Solicitacao de entrada no mundo para objectId={}", objectId);
		validateAndEnterWorld(objectId, client);
	}

	private static void validateAndEnterWorld(final int objectId, final AionConnection client) {
		Account account = client.getAccount();
		PlayerAccountData playerAccData = account.getPlayerAccountData(objectId);

		if (playerAccData == null) {
			client.sendPacket(new SM_ENTER_WORLD_CHECK(Msg.CONNECTION_ERROR));
			return;
		}

		Timestamp lastOnline = playerAccData.getPlayerCommonData().getLastOnline();
		if (lastOnline != null && client.getAccount() != null
				&& client.getAccount().getAccessLevel() < AdminConfig.GM_PANEL) {
			if (System.currentTimeMillis() - lastOnline.getTime() < (GSConfig.CHARACTER_REENTRY_TIME * 1000L)) {
				log.info("[ENTER_WORLD] Reentry delay ativo para objectId={}", objectId);
				client.sendPacket(new SM_ENTER_WORLD_CHECK(Msg.REENTRY_TIME));
				return;
			}
		}

		if (!enteringWorld.add(objectId)) {
			log.warn("Skipping concurrent enter world for {}", objectId);
			return;
		}

		try {
			if (World.getInstance().getPlayer(objectId) != null) {
				log.warn("Duplicate character in world on enter world: {}", objectId);
				client.sendPacket(new SM_ENTER_WORLD_CHECK(Msg.REENTRY_TIME));
				return;
			}

			enterWorld(client, objectId, playerAccData);
		} catch (Throwable ex) {
			log.error("Error during enter world {}", objectId, ex);
			Player player = client.getActivePlayer();
			if (player != null) {
				cleanupFailedEnterWorld(client, player);
			}
			client.sendPacket(new SM_ENTER_WORLD_CHECK(Msg.CONNECTION_ERROR));
		} finally {
			enteringWorld.remove(objectId);
		}
	}

	public static void enterWorld(AionConnection client, int objectId) {
		Account account = client.getAccount();
		if (account == null) {
			log.warn("[ENTER_WORLD] enterWorld chamado sem account valida para objectId={}", objectId);
			client.sendPacket(new SM_ENTER_WORLD_CHECK(Msg.CONNECTION_ERROR));
			return;
		}
		PlayerAccountData playerAccData = account.getPlayerAccountData(objectId);
		if (playerAccData == null) return;
		enterWorld(client, objectId, playerAccData);
	}

	private static void enterWorld(AionConnection client, int objectId, PlayerAccountData playerAccData) {
		Account account = client.getAccount();
		final Player player = PlayerService.getPlayer(objectId, account);

		if (player != null && client.setActivePlayer(player)) {
			player.setClientConnection(client);
			com.lostacademy.lostsocket.core.WebSocketServer.getInstance().bindIfSingleOrLocal(player);
			log.info("[MAC_AUDIT] Player {} has entered world with {} MAC.", player.getName(), client.getMacAddress());
			PlayerCommonData pcd = player.getCommonData();

			client.resetPingFailCount();
			pcd.setOnline(true);
			player.getFriendList().setStatus(Status.ONLINE, pcd);
			PlayerDAO.onlinePlayer(player, true);
			PlayerDAO.storeLastOnlineTime(player.getObjectId(), new Timestamp(System.currentTimeMillis()));
			pcd.setInEditMode(false);

			World.getInstance().storeObject(player);
			NavData.getInstance().onPlayerEnterMap(player.getWorldId());

			if (validateFortressZone(player))
				validateVortexZone(player);

			player.getController().onLevelChange(PlayerDAO.getOldCharacterLevel(player.getObjectId()), player.getLevel());
			// o onLevelChange só ensina os níveis novos; skill que virou autoLearn depois (as _high do Brawler eram skillBook) nunca chegava a quem
			// já estava no nível. Antes do spawn não sai mensagem, e o SM_SKILL_LIST logo abaixo já leva as novas
			SkillLearnService.learnNewSkills(player, 1, player.getLevel());

			if (pcd.getLastOnline() != null) {
				long secondsOffline = (System.currentTimeMillis() - pcd.getLastOnline().getTime()) / 1000;
				if (secondsOffline > 10 * 60)
					pcd.resetSalvationPoints();

				updateEnergyOfRepose(player, secondsOffline);

				if (secondsOffline > 5 * 60)
					pcd.setDp(0);
			}

			StigmaService.onPlayerLogin(player);
			InstanceService.onPlayerLogin(player);

			// 1. SM_VERSION_CHECK (sync feature flags & HUD visibility) & SM_ENTER_WORLD_CHECK (0x0133)
			client.sendPacket(new SM_VERSION_CHECK());
			client.sendPacket(new SM_ENTER_WORLD_CHECK(player.getObjectId()));

			// 2. Skills: pacote unico com todas as skills aprendidas
			client.sendPacket(new SM_SKILL_LIST(player.getSkillList().getAllSkills()));

			// 3. Cooldowns
			if (player.getSkillCoolDowns() != null) {
				client.sendPacket(new SM_SKILL_COOLDOWN(player, player.getSkillCoolDowns(), false));
			} else {
				client.sendPacket(new SM_SKILL_COOLDOWN(player, Collections.emptyMap(), false));
			}
			if (player.getItemCoolDowns() != null) {
				client.sendPacket(new SM_ITEM_COOLDOWN(player.getItemCoolDowns()));
			} else {
				client.sendPacket(new SM_ITEM_COOLDOWN(Collections.emptyMap()));
			}

			// 4. Titulo ativo (Action 1, 11 bytes canonicos no 5.0)
			client.sendPacket(new SM_TITLE_INFO(pcd.getTitleId()));

			// 5. Animacoes / Motions
			client.sendPacket(new SM_MOTION(player.getMotions().getMotions().values()));

			// 5.1 Classic 5.0 Warmup Sequence (from official Wireshark PCAP)
			client.sendPacket(new SM_UNK_01C2());
			PlayerWardrobeService.getInstance().onEnterWorld(player); // S 0x122, logo antes do 0x138 como na captura
			client.sendPacket(new SM_UNK_0138());
			StorybookService.onEnterWorld(player); // S 0x14C e 0x14D
			MorosService.onEnterWorld(player); // S 0x169, logo depois do 0x14D como na captura
			com.lostacademy.lostsocket.secure.SecureAreaService.getInstance().onEnterWorld(player); // S 0x16B (SM_ALTER_INFO)
			client.sendPacket(new SM_UNK_0177());
			client.sendPacket(new SM_UNK_0197(player.getObjectId()));
			client.sendPacket(new SM_UNK_01A8(player.getObjectId()));
			client.sendPacket(new SM_UNK_01BA());

			// 6. Tutorial Hint (MANDATORIO para o cliente Classic 5.0 fechar carregamento e enviar CM_LEVEL_READY)
			client.sendPacket(new SM_TUTORIAL_HINT());
			client.sendPacket(new SM_UNK_0109());

			// 7. UI Settings & Shortcuts
			byte[] uiSettings = player.getPlayerSettings().getUiSettings();
			byte[] shortcuts = player.getPlayerSettings().getShortcuts();
			if (uiSettings != null) {
				client.sendPacket(new SM_UI_SETTINGS(uiSettings, 0));
			}
			if (shortcuts != null) {
				client.sendPacket(new SM_UI_SETTINGS(shortcuts, 1));
			}
			client.sendPacket(new SM_UNK_01C0());

			// 8. Inventario: equipados primeiro (isFirst=true), nao-equipados em blocos de 10 (isFirst=false), terminador vazio, status, estigmas
			sendItemInfos(client, player);

			// 9. SM_LOAD_EQUIPMENT_CHANGE
			PacketSendUtility.sendPacket(player, new SM_LOAD_EQUIPMENT_CHANGE(player));

			playerLoggedIn(player);

			// 9.1 Channel & Bind Point
			client.sendPacket(new SM_CHANNEL_INFO(player.getPosition()));
			TeleportService.sendObeliskBindPoint(player);
			client.sendPacket(new SM_UNK_0146(player.getObjectId()));

			// 11. World & Time & Warehouse
			player.setState(CreatureState.ACTIVE);
			client.sendPacket(new SM_PLAYER_SPAWN(player));
			client.sendPacket(new SM_GAME_TIME());
			client.sendPacket(new SM_UNK_0151());
			sendWarehouseItemInfos(client, player);

			// 12. Tax Info, Dungeon Cooltimes, Abyss Rank, Status Info
			client.sendPacket(new SM_PRICES());
			client.sendPacket(new SM_INSTANCE_INFO((byte) 2, player));
			client.sendPacket(new SM_ABYSS_RANK(player));
			client.sendPacket(new SM_UNK_0191());
			client.sendPacket(new SM_STATS_INFO(player));
			CombatTalentRewardService.sendProgress(player);
			QunaService.onEnterWorld(player); // S 0x11B com o saldo da conta; o oficial não manda no login (lê do STS)

			// 13. Quests: listas primeiro e depois o ADD das que entram agora, na ordem da captura subida-1-60 (908.42 s: listas;
			// 911.67 s: S_QUEST ADD 20153)
			boolean newCharacter = player.getQuestStateList().getAllQuestState().isEmpty();
			QuestEngine.getInstance().sendCompletedQuests(player);
			client.sendPacket(new SM_QUEST_LIST(player.getQuestStateList().getUncompletedQuests()));
			QuestEngine.getInstance().onLevelChanged(player, !newCharacter);


			// 14. Equipe & Servicos sociais
			PlayerAllianceService.onPlayerLogin(player);
			PlayerGroupService.onPlayerLogin(player);
			PetService.getInstance().onPlayerLogin(player);
			MailService.onPlayerLogin(player);
			BrokerService.getInstance().onPlayerLogin(player);
			GlobalTradeService.getInstance().onPlayerLogin(player);
			WeaponFusionSplitService.onPlayerLogin(player);

			// 15. Macro list
			sendMacroList(client, player);

			// 16. S_CUR_STATUS (1) - status carregando no 5.0
			client.sendPacket(new SM_FRIEND_STATUS(1));
			if (player.isLegionMember()) {
				LegionService.getInstance().onLogin(player);
			}

			// 17. Receitas & Stats
			client.sendPacket(new SM_RECIPE_LIST(player.getRecipeList().getRecipeList()));
			com.aionemu.gameserver.services.craft.SielAnvilService.sendProgress(player);
			player.getLifeStats().updateCurrentStats();

			// 18. Tarefas de expiracao
			for (StorageType st : StorageType.values()) {
				IStorage storage = player.getStorage(st.getId());
				if (storage == null)
					continue;
				for (Item item : storage.getItemsWithKinah()) {
					if (item.getExpireTime() > 0)
						ExpireTimerTask.getInstance().registerExpirable(item, player);
				}
			}
			for (Item item : player.getEquipment().getEquippedItems()) {
				if (item.getExpireTime() > 0)
					ExpireTimerTask.getInstance().registerExpirable(item, player);
			}
			for (Motion motion : player.getMotions().getMotions().values()) {
				if (motion.getExpireTime() != 0)
					ExpireTimerTask.getInstance().registerExpirable(motion, player);
			}
			for (Emotion emotion : player.getEmotions().getEmotions()) {
				if (emotion.getExpireTime() != 0)
					ExpireTimerTask.getInstance().registerExpirable(emotion, player);
			}
			for (Title title : player.getTitleList().getTitles()) {
				if (title.getExpireTime() != 0)
					ExpireTimerTask.getInstance().registerExpirable(title, player);
			}

			player.getController().addTask(TaskId.PLAYER_UPDATE,
				ThreadPoolManager.getInstance().scheduleAtFixedRate(new GeneralUpdateTask(player.getObjectId()),
					PeriodicSaveConfig.PLAYER_GENERAL * 1000L, PeriodicSaveConfig.PLAYER_GENERAL * 1000L));
			player.getController().addTask(TaskId.INVENTORY_UPDATE,
				ThreadPoolManager.getInstance().scheduleAtFixedRate(new ItemUpdateTask(player.getObjectId()),
					PeriodicSaveConfig.PLAYER_ITEMS * 1000L, PeriodicSaveConfig.PLAYER_ITEMS * 1000L));

			// 19. Chat & Seguranca
			client.sendPacket(new SM_CHAT_ACCUSE(player));
			client.sendPacket(new SM_SPAM_FILTER_FLAG(player));
			client.sendPacket(new SM_CHANNEL_CHATTING_BLACKLIST_SETTING());
		} else {
			log.warn("[ENTER_WORLD] Falha ao ativar player. objectId={}, player={}, setActivePlayer_ok={}",
				objectId, player, player != null);
			if (player != null) {
				client.setActivePlayer(null);
			}
			client.sendPacket(new SM_ENTER_WORLD_CHECK(Msg.CONNECTION_ERROR));
		}
	}

	private static void cleanupFailedEnterWorld(AionConnection client, Player player) {
		try {
			player.getController().delete();
			player.getCommonData().setOnline(false);
			PlayerDAO.onlinePlayer(player, false);
		} catch (Throwable t) {
			log.error("Failed to cleanup player after enter world error", t);
		}
		player.setClientConnection(null);
		client.setActivePlayer(null);
	}

	private static void sendWarehouseItemInfos(AionConnection client, Player player) {
		WarehouseService.sendWarehouseInfo(player, true);
		for (int i = StorageType.PET_BAG_MIN - 2; i <= StorageType.PET_BAG_MAX; i++) {
			IStorage storage = player.getStorage(i);
			if (storage == null || storage.getItemsWithKinah().isEmpty()) {
				client.sendPacket(new SM_WAREHOUSE_INFO(null, i, 0, true, player));
				continue;
			}
			List<Item> items = storage.getItemsWithKinah();
			SM_WAREHOUSE_INFO.split(items, i, 0, player).forEach(client::sendPacket);
			client.sendPacket(new SM_WAREHOUSE_INFO(null, i, 0, false, player));
		}
		// 5.0 Classic: Inicializa a janela de estigmas (Storage 58) e o slot de síntese/enchant (Storage 59)
		List<Item> stigmaItems = player.getEquipment().getEquippedItemsAllStigma();
		SM_WAREHOUSE_INFO.split(stigmaItems, StorageType.STIGMA.getId(), 0, player).forEach(client::sendPacket);
		client.sendPacket(new SM_WAREHOUSE_INFO(null, StorageType.STIGMA_ENCHANT.getId(), 0, true, player));
	}

	private static void sendItemInfos(AionConnection client, Player player) {
		int questExpands = player.getQuestExpands();
		int npcExpands = player.getNpcExpands();
		player.getInventory().setLimit(StorageType.CUBE.getLimit() + (questExpands + npcExpands) * 9);
		player.getWarehouse().setLimit(StorageType.REGULAR_WAREHOUSE.getLimit() + player.getWarehouseExpansions() * 8);
		Storage inventory = player.getInventory();
		final int CHUNK_SIZE_EQUIP = 4;
		final int CHUNK_SIZE_INVEN = 8;
		boolean isFirstPacket = true;

		List<Item> equipedItems = player.getEquipment().getEquippedItems();
		int equipedSize = equipedItems.size();
		for (int index = 0; index < equipedSize; index += CHUNK_SIZE_EQUIP) {
			int end = Math.min(index + CHUNK_SIZE_EQUIP, equipedSize);
			client.sendPacket(new SM_INVENTORY_INFO(isFirstPacket, equipedItems.subList(index, end), npcExpands,
				questExpands, player));
			isFirstPacket = false;
		}

		List<Item> unequipedItems = inventory.getItemsWithKinah();
		int unequipedSize = unequipedItems.size();
		for (int index = 0; index < unequipedSize; index += CHUNK_SIZE_INVEN) {
			int end = Math.min(index + CHUNK_SIZE_INVEN, unequipedSize);
			client.sendPacket(new SM_INVENTORY_INFO(isFirstPacket, unequipedItems.subList(index, end), npcExpands,
				questExpands, player));
			isFirstPacket = false;
		}

		if (isFirstPacket) {
			client.sendPacket(new SM_INVENTORY_INFO(true, Collections.emptyList(), npcExpands, questExpands, player));
		}

		client.sendPacket(new SM_INVENTORY_INFO());
		client.sendPacket(SM_CUBE_UPDATE.stigmaSlots(player.getCommonData().getAdvencedStigmaSlotSize()));
	}

	private static void sendMacroList(AionConnection client, Player player) {
		SplitList<Macros.Macro> macroSplitList = new DynamicServerPacketBodySplitList<>(player.getMacros().getAll(), true, SM_MACRO_LIST.STATIC_BODY_SIZE,
			SM_MACRO_LIST.DYNAMIC_BODY_PART_SIZE_CALCULATOR);
		macroSplitList.forEach(part -> PacketSendUtility.sendPacket(player, new SM_MACRO_LIST(player.getObjectId(), part, part.isFirst())));
	}

	private static void playerLoggedIn(Player player) {
		log.info("Player Logged In: {} Account: {}", player.getName(), player.getClientConnection().getAccount().getName());
		player.getCommonData().setOnline(true);
		PlayerDAO.onlinePlayer(player, true);
		NavData.getInstance().onPlayerEnterMap(player.getWorldId());
	}

	@SuppressWarnings("lossy-conversions")
	private static void updateEnergyOfRepose(Player player, long secondsOffline) {
		player.getCommonData().updateMaxRepose();
		if (player.getCommonData().isReadyForReposeEnergy() && secondsOffline > 4 * 3600) {
			double hours = secondsOffline / 3600d;
			long addReposeEnergy = Math.round((hours / 48) * player.getCommonData().getMaxReposeEnergy());
			House house = player.getActiveHouse();
			if (house != null) {
				HouseAddress hPos = house.getAddress();
				if (player.getWorldId() == hPos.getMapId()
					&& PositionUtil.isInRange(player.getX(), player.getY(), player.getZ(), hPos.getX(), hPos.getY(), hPos.getZ(), 7))
					addReposeEnergy *= house.getHouseType() == HouseType.STUDIO ? 1.05f : 1.10f;
			}
			player.getCommonData().addReposeEnergy(addReposeEnergy);
		}
	}

	private static boolean validateFortressZone(Player player) {
		FortressLocation fortress = SiegeService.getInstance().findFortress(player.getWorldId(), player.getX(), player.getY(), player.getZ());
		if (fortress != null && fortress.isVulnerable() && fortress.isEnemy(player)) {
			long lastOnlineMillis = player.getCommonData().getLastOnline() == null ? 0 : player.getCommonData().getLastOnline().getTime();
			if (lastOnlineMillis < SiegeService.getInstance().getSiege(fortress).getStartTime()) {
				BindPointPosition bind = player.getBindPoint();
				if (bind != null) {
					World.getInstance().setPosition(player, bind.getMapId(), bind.getX(), bind.getY(), bind.getZ(), bind.getHeading());
				} else {
					PlayerInitialData.LocationData start = DataManager.PLAYER_INITIAL_DATA.getSpawnLocation(player.getRace());
					World.getInstance().setPosition(player, start.getMapId(), start.getX(), start.getY(), start.getZ(), start.getHeading());
				}
				return false;
			}
		}
		return true;
	}

	private static void validateVortexZone(Player player) {
		VortexLocation loc = VortexService.getInstance().getLocationByWorld(player.getWorldId());
		if (loc != null && player.getRace().equals(loc.getInvadersRace())) {
			if (loc.isInsideLocation(player) && loc.isActive() && loc.getVortexController().getPassedPlayers().containsKey(player.getObjectId()))
				return;

			int mapId = loc.getHomeWorldId();
			float x = loc.getHomePoint().getX();
			float y = loc.getHomePoint().getY();
			float z = loc.getHomePoint().getZ();
			byte h = loc.getHomePoint().getHeading();
			World.getInstance().setPosition(player, mapId, x, y, z, h);
		}
	}
}

class GeneralUpdateTask implements Runnable {

	private static final Logger log = LoggerFactory.getLogger(GeneralUpdateTask.class);
	private final int playerId;

	GeneralUpdateTask(int playerId) {
		this.playerId = playerId;
	}

	@Override
	public void run() {
		Player player = World.getInstance().getPlayer(playerId);
		if (player != null) {
			try {
				if (player.isDirty(Player.DirtyFlag.ABYSS_RANK)) {
					player.clearDirty(Player.DirtyFlag.ABYSS_RANK);
					AbyssRankDAO.storeAbyssRank(player);
				}
				if (player.isDirty(Player.DirtyFlag.SKILLS)) {
					player.clearDirty(Player.DirtyFlag.SKILLS);
					PlayerSkillListDAO.storeSkills(player);
				}
				if (player.isDirty(Player.DirtyFlag.QUESTS)) {
					player.clearDirty(Player.DirtyFlag.QUESTS);
					PlayerQuestListDAO.store(player);
				}
				PlayerDAO.storePlayer(player);
				for (House house : player.getHouses())
					house.save();
			} catch (Exception ex) {
				log.error("Exception during periodic saving of player " + player.getName(), ex);
			}
		}
	}
}

class ItemUpdateTask implements Runnable {

	private static final Logger log = LoggerFactory.getLogger(ItemUpdateTask.class);
	private final int playerId;

	ItemUpdateTask(int playerId) {
		this.playerId = playerId;
	}

	@Override
	public void run() {
		Player player = World.getInstance().getPlayer(playerId);
		if (player != null && player.isDirty(Player.DirtyFlag.INVENTORY)) {
			try {
				player.clearDirty(Player.DirtyFlag.INVENTORY);
				InventoryDAO.store(player);
				ItemStoneListDAO.save(player);
			} catch (Exception ex) {
				log.error("Exception during periodic saving of player items " + player.getName(), ex);
			}
		}
	}
}
