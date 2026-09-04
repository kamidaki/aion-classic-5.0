package com.aionemu.gameserver.services.player;

import java.sql.Timestamp;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.configs.main.GSConfig;
import com.aionemu.gameserver.configs.main.PeriodicSaveConfig;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.gameobjects.player.emotion.Emotion;
import com.aionemu.gameserver.model.gameobjects.player.motion.Motion;
import com.aionemu.gameserver.model.gameobjects.player.title.Title;
import com.aionemu.gameserver.model.items.storage.IStorage;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.team2.alliance.PlayerAllianceService;
import com.aionemu.gameserver.model.team2.group.PlayerGroupService;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.serverpackets.S_ABYSS_POINT;
import com.aionemu.gameserver.network.aion.serverpackets.S_ADD_SKILL;
import com.aionemu.gameserver.network.aion.serverpackets.S_CHANNEL_CHATTING_BLACKLIST_SETTING;
import com.aionemu.gameserver.network.aion.serverpackets.S_CHAT_ACCUSE;
import com.aionemu.gameserver.network.aion.serverpackets.S_CUR_STATUS;
import com.aionemu.gameserver.network.aion.serverpackets.S_CUSTOM_ANIM;
import com.aionemu.gameserver.network.aion.serverpackets.S_ENTER_WORLD_CHECK;
import com.aionemu.gameserver.network.aion.serverpackets.S_TUTORIAL_HINT;
import com.aionemu.gameserver.network.aion.serverpackets.S_EVENT;
import com.aionemu.gameserver.network.aion.serverpackets.S_INSTANCE_DUNGEON_COOLTIMES;
import com.aionemu.gameserver.network.aion.serverpackets.S_LOAD_CLIENT_SETTINGS;
import com.aionemu.gameserver.network.aion.serverpackets.S_LOAD_INVENTORY;
import com.aionemu.gameserver.network.aion.serverpackets.S_LOAD_ITEM_COOLTIME;
import com.aionemu.gameserver.network.aion.serverpackets.S_LOAD_MACRO;
import com.aionemu.gameserver.network.aion.serverpackets.S_LOAD_SKILL_COOLTIME;
import com.aionemu.gameserver.network.aion.serverpackets.S_LOAD_WAREHOUSE;
import com.aionemu.gameserver.network.aion.serverpackets.S_RECIPE_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.S_SPAM_FILTER_FLAG;
import com.aionemu.gameserver.network.aion.serverpackets.S_STATUS;
import com.aionemu.gameserver.network.aion.serverpackets.S_TAX_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_TIME;
import com.aionemu.gameserver.network.aion.serverpackets.S_TITLE;
import com.aionemu.gameserver.network.aion.serverpackets.S_WORLD;
import com.aionemu.gameserver.network.aion.serverpackets.need.S_LOAD_EQUIPMENT_CHANGE;
import com.aionemu.gameserver.services.BrokerService;
import com.aionemu.gameserver.services.WeaponFusionSplitService;
import com.aionemu.gameserver.services.SkillLearnService;
import com.aionemu.gameserver.services.StigmaService;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.services.legion.LegionService;
import com.aionemu.gameserver.services.mail.MailService;
import com.aionemu.gameserver.services.toypet.PetService;
import com.aionemu.gameserver.services.WarehouseService;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.taskmanager.tasks.ExpireTimerTask;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.utils.rates.Rates;
import com.aionemu.gameserver.world.World;

public final class PlayerEnterWorldService {
    private static final Logger log = LoggerFactory.getLogger("GAMECONNECTION_LOG");
    private static final Set<Integer> pendingEnterWorld = ConcurrentHashMap.newKeySet();

    public static void startEnterWorld(final int objectId, final AionConnection client) {
        log.info("[ENTER_WORLD] Solicitacao de entrada no mundo para objectId={}", objectId);
        validateAndEnterWorld(objectId, client);
    }

    private static void validateAndEnterWorld(final int objectId, final AionConnection client) {
        PlayerAccountData playerAccData = client.getAccount() != null
                ? client.getAccount().getPlayerAccountData(objectId)
                : null;
        if (playerAccData == null || playerAccData.getPlayerCommonData() == null) {
            client.sendPacket(new S_ENTER_WORLD_CHECK((byte) 0));
            return;
        }
        Timestamp lastOnline = playerAccData.getPlayerCommonData().getLastOnline();
        if (lastOnline != null && client.getAccount() != null
                && client.getAccount().getAccessLevel() < AdminConfig.GM_LEVEL) {
            if (System.currentTimeMillis() - lastOnline.getTime() < (GSConfig.CHARACTER_REENTRY_TIME * 1000L)) {
                log.info("[ENTER_WORLD] Reentry delay ativo para objectId={}", objectId);
                client.sendPacket(new S_ENTER_WORLD_CHECK((byte) 6));
                return;
            }
        }
        if (!pendingEnterWorld.add(objectId)) {
            log.warn("Skipping concurrent enter world for {}", objectId);
            return;
        }
        try {
            if (World.getInstance().findPlayer(objectId) != null) {
                log.warn("Duplicate character in world on enter world: {}", objectId);
                client.sendPacket(new S_ENTER_WORLD_CHECK((byte) 6));
                return;
            }
            // OTIMIZACAO: reaproveita o playerAccData ja carregado acima em vez de buscar de novo dentro de enterWorld.
            enterWorld(client, objectId, playerAccData);
        } catch (Throwable ex) {
            log.error("Error during enter world {}", objectId, ex);
            Player player = client.getActivePlayer();
            if (player != null) {
                cleanupFailedEnterWorld(client, player);
            }
            client.sendPacket(new S_ENTER_WORLD_CHECK((byte) 0));
        } finally {
            pendingEnterWorld.remove(objectId);
        }
    }

    /**
     * Ponto de entrada publico mantido por compatibilidade com quem ja chama
     * enterWorld(client, objectId) diretamente. Busca o PlayerAccountData e delega
     * para a versao interna que reaproveita esse valor.
     */
    public static void enterWorld(AionConnection client, int objectId) {
        Account account = client.getAccount();
        if (account == null) {
            // FIX: protege contra NPE se este metodo for chamado externamente sem
            // passar pelo validateAndEnterWorld (que ja garante account != null).
            log.warn("[ENTER_WORLD] enterWorld chamado sem account valida para objectId={}", objectId);
            client.sendPacket(new S_ENTER_WORLD_CHECK((byte) 0));
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
            log.info("[MAC_AUDIT] Player {} (account {}) has entered world with {} MAC.", player.getName(), account.getName(), client.getMacAddress());
            World.getInstance().storeObject(player);
            /*
            ================= DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
                                E VALIDAR SE ELA REALMENTE EXISTE NO CLASSIC 5.0


            if (playerAccData.getPlayerCommonData().getLastOnline() != null) {
                long lastOnline = playerAccData.getPlayerCommonData().getLastOnline().getTime();
                PlayerCommonData pcd = player.getCommonData();
                long secondsOffline = (System.currentTimeMillis() / 1000) - lastOnline / 1000;
                if (pcd.isReadyForSalvationPoints()) {
                    // The level of "Energy of Salvation" will now be maintained up to 4 hour after
                    // disconnect.
                    if (secondsOffline > 240 * 60) {
                        player.getCommonData().resetSalvationPoints();
                    }
                }
                if (pcd.isReadyForReposteEnergy()) {
                    pcd.updateMaxReposte();
                    if (secondsOffline > 60 * 60) {
                        double hours = Math.round(secondsOffline / 3600.0);
                        long maxRespose = player.getCommonData().getMaxReposteEnergy();
                        long reposePerHour = (maxRespose * 4) / 100;
                        if (hours > 24.0) {
                            hours = 24.0;
                        }
                        long addResposeEnergy = Math.round(hours * reposePerHour);
                        addResposeEnergy = (long) ((float) addResposeEnergy * 1.1);
                        pcd.addReposteEnergy(addResposeEnergy > maxRespose ? maxRespose : addResposeEnergy);
                    }
                }
                if (System.currentTimeMillis() / 1000 - lastOnline > 300) {
                    player.getCommonData().setDp(0);
                }
            }
            */
            StigmaService.onPlayerLogin(player);
            InstanceService.onPlayerLogin(player);

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
            AbyssSkillService.onEnterWorld(player);
            SerialKillerService.getInstance().onLogin(player);
            */
            SkillLearnService.addMissingSkills4P(player);

            client.sendPacket(new S_ENTER_WORLD_CHECK(player.getObjectId()));
            client.sendPacket(new S_ADD_SKILL(player));

            if (player.getSkillCoolDowns() != null) {
                client.sendPacket(new S_LOAD_SKILL_COOLTIME(player.getSkillCoolDowns()));
            } else {
                // FIX: mesma logica de fallback ja usada para item cooldown, para nao deixar
                // o client com um estado de cooldown de skill "preso" de uma sessao anterior.
                client.sendPacket(new S_LOAD_SKILL_COOLTIME(Collections.emptyMap()));
            }
            if (player.getItemCoolDowns() != null) {
                client.sendPacket(new S_LOAD_ITEM_COOLTIME(player.getItemCoolDowns()));
            } else {
                client.sendPacket(new S_LOAD_ITEM_COOLTIME(Collections.emptyMap()));
            }

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO

            List<QuestState> questList = new ArrayList<>();
            List<QuestState> completeQuestList = new ArrayList<>();
            for (QuestState qs : player.getQuestStateList().getAllQuestState()) {
                if (qs.getStatus() == QuestStatus.NONE && qs.getCompleteCount() == 0) {
                    continue;
                }
                if (qs.getStatus() != QuestStatus.COMPLETE && qs.getStatus() != QuestStatus.NONE) {
                    questList.add(qs);
                }
                if (qs.getCompleteCount() > 0) {
                    completeQuestList.add(qs);
                }
            }
            client.sendPacket(new S_LOAD_FINISHEDQUEST(completeQuestList));
            client.sendPacket(new S_LOAD_WORKINGQUEST(questList));
            /*
             * As duas capturas discordam aqui: o personagem antigo recebe a acao 1 (11 bytes) e o
             * recem-criado a acao 2 (5 bytes, `02 01 00 00 00`), e a regra que escolhe entre elas
             * nao foi identificada. Ficamos com a acao 1, cujo layout foi medido no
             * 01_Login_World; a acao 2 continua disponivel em S_TITLE.emUso().
             */
            client.sendPacket(new S_TITLE(player.getCommonData().getTitleId()));
            client.sendPacket(new S_CUSTOM_ANIM(player.getMotions().getMotions().values()));
            /*
             * Sem este pacote o cliente 5.0 nao conclui o carregamento da cena: ele nunca manda o
             * CM_LEVEL_READY e volta para a tela de personagem. Descoberto por bisseccao,
             * reproduzindo a rajada da captura oficial e cortando-a pela metade ate sobrar um:
             * de 58 pacotes ausentes, este era o unico necessario.
             *
             * O corpo e o mesmo da captura -- writeH(0) + writeC(0) = `00 00 00`.
             */
            client.sendPacket(new S_TUTORIAL_HINT());

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
            BattlePassService.getInstance().onEnterWorld(player);
            PlayerWardrobeService.getInstance().onEnterWorld(player);
            */


            byte[] uiSettings = player.getPlayerSettings().getUiSettings();
            byte[] shortcuts = player.getPlayerSettings().getShortcuts();
            if (uiSettings != null) {
                client.sendPacket(new S_LOAD_CLIENT_SETTINGS(uiSettings, 0));
            }
            if (shortcuts != null) {
                client.sendPacket(new S_LOAD_CLIENT_SETTINGS(shortcuts, 1));
            }
            sendItemInfos(client, player);

            PacketSendUtility.sendPacket(player, new S_LOAD_EQUIPMENT_CHANGE(player));

            playerLoggedIn(player);

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO


            client.sendPacket(new S_CHANGE_CHANNEL(player.getPosition()));
            KiskService.getInstance().onLogin(player);

             */

            TeleportService.sendSetBindPoint(player);

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO

            client.sendPacket(new S_USER_BIND_STONE_INFO(player));
            */

            player.setState(CreatureState.ACTIVE);
            client.sendPacket(new S_WORLD(player));
            client.sendPacket(new S_TIME());
            sendWarehouseItemInfos(client, player);

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
            client.sendPacket(new S_TITLE(player));
            client.sendPacket(new S_ADDREMOVE_SOCIAL((byte) 0, player.getEmotions().getEmotions()));
            SiegeService.getInstance().onPlayerLogin(player);
             */

            client.sendPacket(new S_TAX_INFO());
            client.sendPacket(new S_INSTANCE_DUNGEON_COOLTIMES(player, false, player.getCurrentTeam()));
            client.sendPacket(new S_ABYSS_POINT(player.getAbyssRank()));
            client.sendPacket(new S_STATUS(player));
            // Na 5.0 oficial, mensagens de chat (S_MESSAGE) nao sao enviadas durante a tela de loading.
            player.setRates(Rates.getRatesFor(client.getAccount().getMembership()));

            // Buff.
            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
             * if (player.getMembership() >= 0) {
             * SkillEngine.getInstance().applyEffectDirectly(2358, player, player, 0);
             * //[Event] A Noble's Blessing.
             * }
             */

            PlayerAllianceService.onPlayerLogin(player);
            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
            if (player.isInPrison()) {
                PunishmentService.updatePrisonStatus(player);
            }
            if (player.isNotGatherable()) {
                PunishmentService.updateGatherableStatus(player);
            }

            */
            PlayerGroupService.onPlayerLogin(player);
            PetService.getInstance().onPlayerLogin(player);
            MailService.getInstance().onPlayerLogin(player);
            BrokerService.getInstance().onPlayerLogin(player);
            WeaponFusionSplitService.onPlayerLogin(player);
            sendMacroList(client, player);
            client.sendPacket(new S_CUR_STATUS((byte) 1));
            if (player.isLegionMember()) {
                LegionService.getInstance().onLogin(player);
            }

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
            EventWindowService.getInstance().onEnterWorld(player);
            SielEnergyService.getInstance().onLogin(player);
             */

            client.sendPacket(new S_RECIPE_LIST(player.getRecipeList().getRecipeList()));
            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
            PetitionService.getInstance().onPlayerLogin(player);
            if (AutoGroupConfig.AUTO_GROUP_ENABLED) {
                AutoGroupService.getInstance().onPlayerLogin(player);
            }

            ClassChangeService.showClassChangeDialog(player);
            GMService.getInstance().onPlayerLogin(player);
             */

            player.getLifeStats().updateCurrentStats();
            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO
            player.getEquipment().checkRankLimitItems();
            player.getNpcFactions().sendDailyQuest();

             */
            for (StorageType st : StorageType.values()) {
                if (st == StorageType.LEGION_WAREHOUSE) {
                    continue;
                }
                IStorage storage = player.getStorage(st.getId());
                if (storage != null) {
                    for (Item item : storage.getItemsWithKinah()) {
                        if (item.getExpireTime() > 0) {
                            ExpireTimerTask.getInstance().addTask(item, player);
                        }
                    }
                }
            }
            for (Item item : player.getEquipment().getEquippedItems()) {
                if (item.getExpireTime() > 0) {
                    ExpireTimerTask.getInstance().addTask(item, player);
                }
            }
            for (Motion motion : player.getMotions().getMotions().values()) {
                if (motion.getExpireTime() != 0) {
                    ExpireTimerTask.getInstance().addTask(motion, player);
                }
            }
            for (Emotion emotion : player.getEmotions().getEmotions()) {
                if (emotion.getExpireTime() != 0) {
                    ExpireTimerTask.getInstance().addTask(emotion, player);
                }
            }
            for (Title title : player.getTitleList().getTitles()) {
                if (title.getExpireTime() != 0) {
                    ExpireTimerTask.getInstance().addTask(title, player);
                }
            }
            player.getController().addTask(TaskId.PLAYER_UPDATE,
                    ThreadPoolManager.getInstance().scheduleAtFixedRate(new GeneralUpdateTask(player.getObjectId()),
                            PeriodicSaveConfig.PLAYER_GENERAL * 1000L, PeriodicSaveConfig.PLAYER_GENERAL * 1000L));
            player.getController().addTask(TaskId.INVENTORY_UPDATE,
                    ThreadPoolManager.getInstance().scheduleAtFixedRate(new ItemUpdateTask(player.getObjectId()),
                            PeriodicSaveConfig.PLAYER_ITEMS * 1000L, PeriodicSaveConfig.PLAYER_ITEMS * 1000L));

            /* DESATIVADO TEMPORÁRIAMENTE ATÉ CHEGAR NO DESENVOLVIMENTO DESSA FUNÇÃO

            player.getController().addTask(TaskId.REPOSE_ENERGY_TASK, ThreadPoolManager.getInstance()
                    .scheduleAtFixedRate(new ReposeEnergyTask(player.getObjectId()), 1200 * 1000, 1200 * 1000));
            if (EventsConfig.ENABLE_EVENT_SERVICE) {
                EventService.getInstance().onPlayerLogin(player);
            }
            BoostEventService.getInstance().boostEventLogin(player);
            RelinquishCraftStatus.removeExcessCraftStatus(player, false);
            BlackCloudTradeService.getInstance().onLogin(player);


             */
            // Chat & Seguranca
            client.sendPacket(new S_CHAT_ACCUSE(player));
            client.sendPacket(new S_SPAM_FILTER_FLAG(player));
            client.sendPacket(new S_CHANNEL_CHATTING_BLACKLIST_SETTING());

            // Diagnostico, desligado por padrao: ver RajadaOficial.
            RajadaOficial.envia(client, player);
        } else {
            // FIX: antes este ramo so logava e deixava o cliente preso na tela de loading,
            // pois nenhum pacote de resposta era enviado quando player==null ou setActivePlayer falhava.
            log.warn("[ENTER_WORLD] Falha ao ativar player. objectId={}, player={}, setActivePlayer_ok={}",
                    objectId, player, player != null);
            if (player != null) {
                // player foi carregado por PlayerService.getPlayer, mas nao foi anexado a conexao
                // nem armazenado no World (storeObject so roda dentro deste if). Nao ha, portanto,
                // limpeza de World/controller a fazer aqui - so garantimos que a conexao nao fique
                // com referencia inconsistente.
                client.setActivePlayer(null);
            }
            client.sendPacket(new S_ENTER_WORLD_CHECK((byte) 0));
        }
    }

    /**
     * Centraliza a limpeza usada quando o enter world falha apos o player ja ter sido
     * armazenado no World / anexado a conexao (extraido do catch original para evitar
     * duplicacao com o novo ramo de falha em enterWorld).
     */
    private static void cleanupFailedEnterWorld(AionConnection client, Player player) {
        try {
            player.getController().delete();
            player.getCommonData().setOnline(false);
            DAOManager.getDAO(PlayerDAO.class).onlinePlayer(player, false);
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
                client.sendPacket(new S_LOAD_WAREHOUSE(null, i, 0, true, player));
                continue;
            }
            List<Item> items = storage.getItemsWithKinah();
            int itemsSize = items.size();
            for (int index = 0; index < itemsSize; index += 10) {
                int end = Math.min(index + 10, itemsSize);
                client.sendPacket(new S_LOAD_WAREHOUSE(items.subList(index, end), i, 0, index == 0, player));
            }
            client.sendPacket(new S_LOAD_WAREHOUSE(null, i, 0, false, player));
        }
    }

    private static void sendItemInfos(AionConnection client, Player player) {
        int questExpands = player.getQuestExpands();
        int npcExpands = player.getNpcExpands();
        player.getInventory().setLimit(StorageType.CUBE.getLimit() + (questExpands + npcExpands) * 9);
        player.getWarehouse().setLimit(StorageType.REGULAR_WAREHOUSE.getLimit() + player.getWarehouseSize() * 8);
        Storage inventory = player.getInventory();
        List<Item> equipedItems = player.getEquipment().getEquippedItems();
        if (!equipedItems.isEmpty()) {
            client.sendPacket(new S_LOAD_INVENTORY(true, player.getEquipment().getEquippedItems(), npcExpands,
                    questExpands, player));
        }
        List<Item> unequipedItems = inventory.getItemsWithKinah();
        int itemsSize = unequipedItems.size();
        if (itemsSize != 0) {
            int index = 0;
            while (index + 10 < itemsSize) {
                client.sendPacket(new S_LOAD_INVENTORY(false, unequipedItems.subList(index, index + 10), npcExpands,
                        questExpands, player));
                index += 10;
            }
            client.sendPacket(new S_LOAD_INVENTORY(false, unequipedItems.subList(index, itemsSize), npcExpands,
                    questExpands, player));
        }
        client.sendPacket(new S_LOAD_INVENTORY());
        client.sendPacket(new S_STATUS(player));
        client.sendPacket(S_EVENT.stigmaSlots(player.getCommonData().getAdvencedStigmaSlotSize()));
    }

    private static void sendMacroList(AionConnection client, Player player) {
        client.sendPacket(new S_LOAD_MACRO(player, false));
        if (player.getMacroList().getSize() > 7) {
            client.sendPacket(new S_LOAD_MACRO(player, true));
        }
    }

    private static void playerLoggedIn(Player player) {
        log.info("Player Logged In: {} Account: {}", player.getName(), player.getClientConnection().getAccount().getName());
        player.getCommonData().setOnline(true);
        DAOManager.getDAO(PlayerDAO.class).onlinePlayer(player, true);
        player.onLoggedIn();
        player.setOnlineTime();
    }
}