package com.aionemu.gameserver.network.aion.clientpackets;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.utils.NetworkUtils;
import com.aionemu.gameserver.dao.PlayerAppearanceDAO;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.player.PendingCharacterEdit;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_PLASTIC_SURGERY;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.audit.AuditLogger;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_CHARACTER_EDIT extends AbstractCharacterEditPacket {

	private static final Logger log = LoggerFactory.getLogger(CM_CHARACTER_EDIT.class);

	private int objectId;
	private byte[] raw;

	public CM_CHARACTER_EDIT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		// copia crua para o log: a expressao escolhida na tela nao chegava ao banco (30/09, Glad salvo com expression 0)
		raw = readB(getRemainingBytes());
		setBuffer(ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN));
		objectId = readD();
		readBasicInfo(false);
		readAppearance();
	}

	@Override
	protected void runImpl() {
		AionConnection client = getConnection();
		if (client.getAccount() == null)
			return;
		log.info("[CHARACTER_EDIT] C_EDIT_CHARACTER ({} b) objectId={} face={} hair={} deco={} tattoo={} contour={} expression={} faceExpression={}{}{}", raw.length, objectId,
			playerAppearance.getFace(), playerAppearance.getHair(), playerAppearance.getDeco(), playerAppearance.getTattoo(), playerAppearance.getFaceContour(),
			playerAppearance.getExpression(), playerAppearance.getFaceExpression(), System.lineSeparator(), NetworkUtils.toHex(ByteBuffer.wrap(raw)));

		PlayerAccountData playerAccData = client.getAccount().getPlayerAccountData(objectId);
		// so o servidor abre a tela (NPC ou Aion Look); sem o modo edicao o pacote vem forjado
		if (playerAccData == null || !playerAccData.getPlayerCommonData().isInEditMode())
			return;

		// No cancelamento o cliente pede a volta ao mundo com C_ENTER_WORLD e depois volta a pedir a lista de personagens normalmente (30/09 22:51).
		// Quando era o servidor que empurrava o mundo daqui, o cliente ficava preso na edicao e nunca mais pedia o C 0x5E, nem reconectando.
		// Por isso a edicao fica pendente e o cliente recebe a resposta do proprio pedido, como no CREATE/DELETE/RESTORE_CHARACTER (valor 0, ver SM_PLASTIC_SURGERY); ela e
		// aplicada no C_ENTER_WORLD (applyPendingEdit)
		playerAccData.getPlayerCommonData().setPendingCharacterEdit(new PendingCharacterEdit(gender, playerAppearance));
		sendPacket(SM_PLASTIC_SURGERY.editResult(objectId, playerAccData.getPlayerCommonData().getGender() != gender));
		log.info("[CHARACTER_EDIT] Edicao pendente para objectId={}; aguardando C_ENTER_WORLD", objectId);
	}

	/**
	 * Chamado pelo C_ENTER_WORLD vindo da tela de edicao, logo depois do enterWorld. O ticket sai sempre, GM inclusive.
	 */
	public static void applyPendingEdit(Player player, PendingCharacterEdit edit) {
		boolean isGenderSwitch = player.getGender() != edit.gender();
		if (!checkOrRemoveTicket(player, isGenderSwitch, true)) {
			AuditLogger.log(player, "tried to apply their plastic surgery without a ticket.");
			log.warn("[CHARACTER_EDIT] {} confirmou a edicao sem ticket de {}; nada aplicado", player.getName(), isGenderSwitch ? "genero" : "aparencia");
			return;
		}
		if (isGenderSwitch) {
			player.getCommonData().setGender(edit.gender());
			PlayerDAO.storeGender(player.getObjectId(), edit.gender());
		}
		player.setPlayerAppearance(edit.appearance());
		PlayerAppearanceDAO.store(player);
		// ainda antes do spawn: o SM_PLAYER_INFO do CM_LEVEL_READY ja leva a aparencia nova
		if (player.isSpawned())
			player.getController().onChangedPlayerAttributes();
		log.info("[CHARACTER_EDIT] Ticket de {} consumido; aparencia aplicada para {}", isGenderSwitch ? "genero" : "aparencia", player.getName());
	}

	/**
	 * Abre a tela de edicao (NPC e Aion Look): S_EDIT_CHARACTER [D obj][C 1 com ticket / 2 sem][C genero] e o cliente responde com
	 * C_ASK_QUIT [01]. Abre mesmo sem ticket, como previa: na captura oficial aionlook.pcapng (30/09, conta sem ticket) veio [C 2], a tela abriu
	 * e o jogador cancelou. O ticket so e cobrado no C_EDIT_CHARACTER.
	 */
	public static void openEditScreen(Player player, boolean isGenderSwitch, String source) {
		log.info("[CHARACTER_EDIT] Abrindo a tela de {} para {} ({}, ticket={})", isGenderSwitch ? "genero" : "aparencia", player.getName(), source,
			checkOrRemoveTicket(player, isGenderSwitch, false));
		PacketSendUtility.sendPacket(player, new SM_PLASTIC_SURGERY(player, isGenderSwitch));
		player.getCommonData().setInEditMode(true);
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
