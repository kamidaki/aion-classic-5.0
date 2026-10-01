package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.dao.PlayerAppearanceDAO;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerEnterWorldService;
import com.aionemu.gameserver.utils.audit.AuditLogger;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_CHARACTER_EDIT extends AbstractCharacterEditPacket {

	private static final Logger log = LoggerFactory.getLogger(CM_CHARACTER_EDIT.class);

	private int objectId;

	public CM_CHARACTER_EDIT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		objectId = readD();
		readBasicInfo(false);
		readAppearance();
	}

	@Override
	protected void runImpl() {
		AionConnection client = getConnection();
		if (client == null || client.getAccount() == null) {
			log.warn("[CHARACTER_EDIT] Conexao ou conta nula para objectId={}", objectId);
			return;
		}

		PlayerAccountData playerAccData = client.getAccount().getPlayerAccountData(objectId);
		if (playerAccData == null) {
			log.warn("[CHARACTER_EDIT] Account {} nao possui personagem com objectId={}", client.getAccount().getName(), objectId);
			return;
		}

		boolean inEditMode = playerAccData.getPlayerCommonData().isInEditMode();
		log.info("[CHARACTER_EDIT] Processando edicao de aparencia para objectId={}, editMode={}", objectId, inEditMode);
		playerAccData.getPlayerCommonData().setInEditMode(false);

		// Retorna o jogador ao mundo para sair da tela de edição
		PlayerEnterWorldService.enterWorld(client, objectId);
		Player player = client.getActivePlayer();
		if (player == null) {
			log.error("[CHARACTER_EDIT] Falha ao obter activePlayer apos enterWorld para objectId={}", objectId);
			return;
		}

		boolean isGenderSwitch = player.getGender() != gender;
		boolean freeEdit = client.getAccount().getAccessLevel() >= AdminConfig.GM_PANEL;
		boolean hasTicket = freeEdit || checkOrRemoveTicket(player, isGenderSwitch, true);

		if (hasTicket) {
			if (isGenderSwitch) {
				player.getCommonData().setGender(gender);
				PlayerDAO.storeGender(objectId, gender);
			}
			player.setPlayerAppearance(playerAppearance);
			PlayerAppearanceDAO.store(player);
			player.getController().onChangedPlayerAttributes();
			log.info("[CHARACTER_EDIT] Aparencia e atributos atualizados com sucesso para player={}", player.getName());
		} else {
			AuditLogger.log(player, "tried to apply their plastic surgery without a ticket.");
			log.warn("[CHARACTER_EDIT] Player {} tentou aplicar cirurgia plastica sem ticket valido.", player.getName());
		}
	}

	public static boolean checkOrRemoveTicket(Player player, boolean isGenderSwitch, boolean removeTicket) {
		int[] ticketIds = isGenderSwitch ? new int[] { 169660000, 169660001, 169660002, 169660003, 169660004 } : new int[] { 169650000, 169650001, 169650002, 169650003, 169650004, 169650005, 169650006, 169650007, 169650008 };
		for (int ticketId : ticketIds) {
			if (removeTicket && player.getInventory().decreaseByItemId(ticketId, 1) || !removeTicket && player.getInventory().getItemCountByItemId(ticketId) > 0) {
				return true;
			}
		}
		return false;
	}
}
