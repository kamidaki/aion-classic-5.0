package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.stats.container.PlayerLifeStats;
import com.aionemu.gameserver.network.aion.serverpackets.S_HIT_POINT;
import com.aionemu.gameserver.network.aion.serverpackets.S_MANA_POINT;
import com.aionemu.gameserver.network.aion.serverpackets.S_CUR_STATUS;
import com.aionemu.gameserver.network.aion.serverpackets.S_FLIGHT_POINT;
import com.aionemu.gameserver.model.gameobjects.Pet;
import com.aionemu.gameserver.model.gameobjects.Summon;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.templates.windstreams.Location2D;
import com.aionemu.gameserver.model.templates.windstreams.WindstreamTemplate;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.services.*;
import com.aionemu.gameserver.services.rift.RiftInformer;
import com.aionemu.gameserver.world.World;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CM_LEVEL_READY extends AionClientPacket {
	private static final Logger log = LoggerFactory.getLogger("GAMECONNECTION_LOG");

	public CM_LEVEL_READY(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		Player activePlayer = getConnection().getActivePlayer();
		if (activePlayer == null) {
			log.warn("[LEVEL_READY] Recebido CM_LEVEL_READY mas activePlayer e null!");
			return;
		}
		log.info("[LEVEL_READY] Recebido CM_LEVEL_READY de " + activePlayer.getName() + " (objectId=" + activePlayer.getObjectId() + ", map=" + activePlayer.getWorldId() + ")");
		if (activePlayer.isSpawned()) {
			log.warn("[LEVEL_READY] activePlayer " + activePlayer.getName() + " ja esta marcado como spawned.");
			return;
		}

		// 1. Invincible time (60s) conforme PCAP oficial (op 0x00FE)
		sendPacket(new S_INVINCIBLE_TIME(60));
		// 2. Renderiza o modelo e avatar 3D do jogador com layout 5.0 oficial (op 0x0020, 333 bytes)
		sendPacket(new S_PUT_USER(activePlayer, false));
		// 3. Invincible time (60000ms) conforme PCAP oficial (op 0x00FE)
		sendPacket(new S_INVINCIBLE_TIME(60000));
		// 4. Cessação de piscar / estado visual no spawn (op 0x0043, 7 bytes)
		sendPacket(new S_INVISIBLE_LEVEL(activePlayer));
		// 5. Nível de permissão/builder (op 0x00EE, 29 bytes)
		boolean isGM = getConnection().getAccount() != null && getConnection().getAccount().getAccessLevel() >= AdminConfig.GM_PANEL;
		sendPacket(new S_BUILDER_LEVEL(isGM));
		// 6. Animações customizadas de pose/movimento (op 0x0093, 19 bytes)
		sendPacket(new S_CUSTOM_ANIM(activePlayer.getObjectId(), activePlayer.getMotions().getActiveMotions()));
		// 7. Comanda o cliente a fechar a cena/HUD de Character Select e entrar no modo de jogo (op 0x008B, 03 00000000 00000000)
		/*
		 * O segundo campo e 20 (0x14), nao 0: `03 14 00 00 00 00 00 00 00` nas quatro ocorrencias
		 * das duas capturas oficiais, em mapas diferentes -- e constante, nao um id de cena.
		 */
		sendPacket(new S_WORLD_SCENE_STATUS(3, 20, 0));
		WindstreamTemplate template = DataManager.WINDSTREAM_DATA
				.getStreamTemplate(activePlayer.getPosition().getMapId());
		Location2D location;
		if (template != null && template.getLocations() != null) {
			for (int i = 0; i < template.getLocations().getLocation().size(); i++) {
				location = template.getLocations().getLocation().get(i);
				if (location != null && location.getFlyPathType() != null) {
					sendPacket(new S_WIND_STATE_INFO(location.getFlyPathType().getId(), template.getMapid(),
							location.getId(), location.getState()));
				}
			}
		}
		location = null;
		template = null;
		if (activePlayer.isSpawned()) {
			World.getInstance().despawn(activePlayer);
		}
		World.getInstance().spawn(activePlayer);
		activePlayer.getController().refreshZoneImpl();
		if (activePlayer.isInSiegeWorld()) {
			SiegeService.getInstance().onEnterSiegeWorld(activePlayer);
		}
		activePlayer.getController().updateZone();
		activePlayer.getController().updateNearbyQuests();
		WeatherService.getInstance().loadWeather(activePlayer);
		QuestEngine.getInstance().onEnterWorld(new QuestEnv(null, activePlayer, 0, 0));
		activePlayer.getController().onEnterWorld();
		RiftInformer.sendRiftsInfo(activePlayer);
		activePlayer.getEffectController().updatePlayerEffectIcons();
		sendPacket(S_EVENT.cubeSize(StorageType.CUBE, activePlayer));
		sendPacket(new S_WIELD(activePlayer.getObjectId(), activePlayer.getEquipment().getEquippedItemsWithoutStigma()));
		Pet pet = activePlayer.getPet();
		if (pet != null && !pet.isSpawned()) {
			World.getInstance().spawn(pet);
		}
		// Summon.
		Summon summon = activePlayer.getSummon();
		if (summon != null && !summon.isSpawned()) {
			World.getInstance().spawn(summon);
		}
		activePlayer.setPortAnimation(0);
		PlayerLifeStats vida = activePlayer.getLifeStats();
		sendPacket(new S_HIT_POINT(vida.getCurrentHp(), activePlayer.getGameStats().getMaxHp().getCurrent()));
		sendPacket(new S_MANA_POINT(vida.getCurrentMp(), activePlayer.getGameStats().getMaxMp().getCurrent()));
		sendPacket(new S_FLIGHT_POINT(vida.getCurrentFp(), vida.getMaxFp()));
		/*
		 * Na captura oficial o S_CUR_STATUS aparece duas vezes: `01` durante a entrada no mundo e
		 * `02` aqui, depois do spawn -- a transicao de "carregando" para "ativo". Nos so
		 * mandavamos o primeiro, e o personagem ficava no mundo mas congelado.
		 */
		sendPacket(new S_CUR_STATUS((byte) 2));
		// Diagnostico, desligado por padrao: ver RajadaOficial.
		com.aionemu.gameserver.services.player.RajadaOficial.enviaPosSpawn(getConnection(), activePlayer);
		log.info("[LEVEL_READY] Personagem " + activePlayer.getName() + " spawnado com sucesso no mundo! Posicao=(" + activePlayer.getX() + ", " + activePlayer.getY() + ", " + activePlayer.getZ() + ")");
	}
}