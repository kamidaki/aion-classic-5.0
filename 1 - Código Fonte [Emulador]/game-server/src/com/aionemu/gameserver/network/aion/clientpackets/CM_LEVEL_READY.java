package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.configs.main.EventsConfig;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.templates.world.WorldMapTemplate;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.lostacademy.nativepath.NativePathConfig;
import com.lostacademy.nativepath.NativePathData;
import com.lostacademy.nav.NavData;
import com.aionemu.gameserver.model.animations.ArrivalAnimation;
import com.aionemu.gameserver.model.gameobjects.Pet;
import com.aionemu.gameserver.model.gameobjects.Summon;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.FlyState;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.stats.container.PlayerLifeStats;
import com.aionemu.gameserver.model.templates.windstreams.Location2D;
import com.aionemu.gameserver.model.templates.windstreams.WindstreamTemplate;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.services.CampWarService;
import com.aionemu.gameserver.services.SiegeService;
import com.aionemu.gameserver.services.TownService;
import com.aionemu.gameserver.services.WeatherService;
import com.aionemu.gameserver.services.event.EventService;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.services.rift.RiftInformer;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.World;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_LEVEL_READY extends AionClientPacket {

	public CM_LEVEL_READY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		Player activePlayer = getConnection().getActivePlayer();
		if (activePlayer == null) {
			return;
		}
		if (activePlayer.isSpawned()) {
			return;
		}

		// 1. Invincible time (60s) conforme PCAP oficial (op 0x00FE)
		sendPacket(new SM_INVINCIBLE_TIME(60));
		// 2. Renderiza o modelo e avatar 3D do jogador com layout 5.0 oficial (op 0x0020, 333 bytes)
		sendPacket(new SM_PLAYER_INFO(activePlayer));
		// 3. Invincible time (60000ms) conforme PCAP oficial (op 0x00FE)
		sendPacket(new SM_INVINCIBLE_TIME(60000));
		// 4. Cessação de piscar / estado visual no spawn (op 0x0043, 7 bytes)
		sendPacket(new SM_PLAYER_STATE(activePlayer));
		// 5. Nível de permissão/builder (op 0x00EE, 29 bytes)
		boolean isGM = getConnection().getAccount() != null && getConnection().getAccount().getAccessLevel() >= AdminConfig.GM_PANEL;
		sendPacket(new SM_ACCOUNT_PROPERTIES(isGM));
		// 6. Animações customizadas de pose/movimento (op 0x0093)
		sendPacket(new SM_MOTION(activePlayer.getObjectId(), activePlayer.getMotions().getActiveMotions()));
		// 7. Comanda o cliente a fechar a cena/HUD de Character Select e entrar no modo de jogo (op 0x008B)
		sendPacket(new SM_WORLD_SCENE_STATUS(3, 20, 0));


		WindstreamTemplate template = DataManager.WINDSTREAM_DATA.getStreamTemplate(activePlayer.getPosition().getMapId());
		if (template != null && template.getLocations() != null) {
			for (Location2D location : template.getLocations().getLocation()) {
				if (location != null && location.getFlyPathType() != null) {
					sendPacket(new SM_WINDSTREAM_ANNOUNCE(location.getFlyPathType().getId(), template.getMapId(), location.getId(), location.getState()));
				}
			}
		}

		if (activePlayer.isSpawned()) {
			World.getInstance().despawn(activePlayer);
		}
		// Spawn player into the world.
		World.getInstance().spawn(activePlayer);

		WorldMapTemplate templateMaps = DataManager.WORLD_MAPS_DATA.getTemplate(activePlayer.getWorldId());
		String mapName = templateMaps != null && templateMaps.getName() != null ? templateMaps.getName() : "ID " + activePlayer.getWorldId();
		boolean hasNativePath = NativePathConfig.NATIVE_PATH_ENABLE && NativePathData.getInstance().hasMap(activePlayer.getWorldId());
		boolean hasNavMesh = GeoDataConfig.GEO_NAV_ENABLE && NavData.getInstance().getNavMap(activePlayer.getWorldId()) != null;
		String navMessage;
		if (hasNativePath) {
			navMessage = String.format("\uE0D0Mapa: %s | Navegação NPC: CryEngine Nativo \uE0CB", mapName);
		} else if (hasNavMesh) {
			navMessage = String.format("\uE0D0Mapa: %s | Navegação NPC: NavMesh (.nav) \uE0CB", mapName);
		} else {
			navMessage = String.format("\uE0D0 Mapa: %s | Navegação NPC: Sem dados disponíveis \uE0CD", mapName);
		}
		PacketSendUtility.sendMessage(activePlayer, navMessage);

		if (activePlayer.isInFlyState(FlyState.FLYING)) // notify client if we are still flying (client always ends flying after teleport)
			activePlayer.getFlyController().startFly(true, true);

		// SM_SHIELD_EFFECT, SM_ABYSS_ARTIFACT_INFO3
		if (activePlayer.isInSiegeWorld()) {
			SiegeService.getInstance().onEnterSiegeWorld(activePlayer);
		}

		// Estado das zonas PvP das torres do mapa (S_ZONE_PVP), que o oficial manda no login junto da lista de zonas.
		CampWarService.getInstance().onEnterWorld(activePlayer);

		// SM_RIFT_ANNOUNCE
		RiftInformer.sendRiftsInfo(activePlayer);

		// SM_UPGRADE_ARCADE
		if (EventsConfig.ENABLE_EVENT_ARCADE)
			sendPacket(new SM_UPGRADE_ARCADE(true));

		// SM_NEARBY_QUESTS
		activePlayer.getController().updateNearbyQuests();

		// SM_QUEST_REPEAT
		activePlayer.getController().updateRepeatableQuests();

		// Loading weather for the player's region
		WeatherService.getInstance().loadWeather(activePlayer);

		QuestEngine.getInstance().onEnterWorld(activePlayer);

		activePlayer.getController().onEnterWorld();
		InstanceService.onEnterInstance(activePlayer);
		activePlayer.getEffectController().updatePlayerEffectIcons(null);
		sendPacket(SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, activePlayer));
		sendPacket(new SM_UPDATE_PLAYER_APPEARANCE(activePlayer.getObjectId(), activePlayer.getEquipment().getEquippedItemsWithoutStigma()));

		Pet pet = activePlayer.getPet();
		if (pet != null && !pet.isSpawned())
			World.getInstance().spawn(pet);
		Summon summon = activePlayer.getSummon();
		if (summon != null && !summon.isSpawned())
			World.getInstance().spawn(summon);

		activePlayer.setPortAnimation(ArrivalAnimation.NONE);

		PlayerLifeStats vida = activePlayer.getLifeStats();
		sendPacket(new SM_STATUPDATE_HP(vida.getCurrentHp(), activePlayer.getGameStats().getMaxHp().getCurrent()));
		sendPacket(new SM_STATUPDATE_MP(vida.getCurrentMp(), activePlayer.getGameStats().getMaxMp().getCurrent()));
		sendPacket(new SM_FLY_TIME(vida.getCurrentFp(), vida.getMaxFp()));
		// Transition from loading to active in 5.0 (unfreezes player character)
		sendPacket(new SM_FRIEND_STATUS(2));

		TownService.getInstance().onEnterWorld(activePlayer);
		EventService.getInstance().onEnterMap(activePlayer);

		var team = activePlayer.getCurrentTeam();
		if (team != null)
			ThreadPoolManager.getInstance().schedule(() -> team.sendBrands(activePlayer), 100); // delayed to fix brands when returning from studios/houses
	}
}
